import unittest

from app import app, bmi_guidance


class BmiAppTests(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()

    def test_initial_page(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        page = response.get_data(as_text=True)
        self.assertIn("了解自己的<br><em>健康狀況。</em>", page)
        self.assertIn("計算你的 BMI", page)
        self.assertIn('name="name"', page)
        self.assertIn('<label for="gender">性別', page)
        self.assertIn('<option value="" selected>請選擇（選填）</option>', page)
        self.assertIn('<option value="不願透露"', page)

    def test_calculation_and_advice(self):
        response = self.client.post("/", data={"height": "170", "weight": "65"})
        page = response.get_data(as_text=True)
        self.assertIn("22.5", page)
        self.assertIn("健康體位", page)
        self.assertIn("維持均衡飲食", page)
        self.assertIn("給你的健康建議", page)

    def test_gender_is_optional_and_does_not_change_bmi_or_category(self):
        for gender in ("", "男性", "女性", "不願透露"):
            with self.subTest(gender=gender):
                response = self.client.post(
                    "/", data={"height": "170", "weight": "65", "gender": gender}
                )
                page = response.get_data(as_text=True)
                self.assertIn("22.5", page)
                self.assertIn("健康體位", page)
                if gender:
                    self.assertIn(f'<p class="result-gender">性別 <strong>{gender}</strong></p>', page)
                    self.assertIn(f'<option value="{gender}" selected>', page)
                else:
                    self.assertNotIn('class="result-gender"', page)

    def test_gender_is_preserved_when_measurements_are_invalid(self):
        response = self.client.post(
            "/", data={"height": "", "weight": "65", "gender": "女性"}
        )
        page = response.get_data(as_text=True)
        self.assertIn('<option value="女性" selected>', page)
        self.assertIn("請輸入大於 0 的有效身高", page)
        self.assertNotIn("YOUR RESULT", page)

    def test_invalid_gender_is_not_selected_or_displayed(self):
        response = self.client.post(
            "/", data={"height": "170", "weight": "65", "gender": "<script>alert(1)</script>"}
        )
        page = response.get_data(as_text=True)
        self.assertIn("22.5", page)
        self.assertIn('<option value="" selected>', page)
        self.assertNotIn('class="result-gender"', page)
        self.assertNotIn("<script>", page)

    def test_name_is_shown_with_advice(self):
        response = self.client.post("/", data={"name": "  小明  ", "height": "170", "weight": "65"})
        page = response.get_data(as_text=True)
        self.assertIn('value="小明"', page)
        self.assertIn("小明，給你的健康建議", page)
        self.assertIn("維持均衡飲食", page)

    def test_name_is_preserved_when_measurements_are_invalid(self):
        response = self.client.post("/", data={"name": "小明", "height": "", "weight": "65"})
        page = response.get_data(as_text=True)
        self.assertIn('value="小明"', page)
        self.assertIn('aria-invalid="true"', page)
        self.assertNotIn("YOUR RESULT", page)

    def test_name_is_escaped_in_form_and_result(self):
        response = self.client.post("/", data={"name": '<script>alert(1)</script>', "height": "170", "weight": "65"})
        page = response.get_data(as_text=True)
        self.assertNotIn("<script>", page)
        self.assertIn("&lt;script&gt;alert(1)&lt;/script&gt;，給你的健康建議", page)

    def test_blank_name_uses_generic_advice(self):
        response = self.client.post("/", data={"name": "   ", "height": "170", "weight": "65"})
        self.assertIn('<h2 id="result-title">給你的健康建議</h2>', response.get_data(as_text=True))

    def test_taiwan_adult_thresholds(self):
        for bmi, category in [
            (18.4, "體重過輕"),
            (18.5, "健康體位"),
            (23.9, "健康體位"),
            (24.0, "體重過重"),
            (26.9, "體重過重"),
            (27.0, "肥胖"),
        ]:
            with self.subTest(bmi=bmi):
                self.assertEqual(bmi_guidance(bmi)["label"], category)

    def test_invalid_fields_do_not_produce_result(self):
        for height, weight in [("", "65"), ("0", "65"), ("abc", "65"), ("170", "-2"), ("inf", "65"), ("170", "nan"), ("1e-300", "65"), ("1e308", "65"), ("1", "1e308")]:
            with self.subTest(height=height, weight=weight):
                response = self.client.post("/", data={"height": height, "weight": weight})
                page = response.get_data(as_text=True)
                self.assertEqual(response.status_code, 200)
                self.assertIn('aria-invalid="true"', page)
                self.assertNotIn("YOUR RESULT", page)

    def test_input_is_escaped(self):
        response = self.client.post("/", data={"height": '<script>alert(1)</script>', "weight": "65"})
        page = response.get_data(as_text=True)
        self.assertNotIn("<script>", page)
        self.assertIn("請輸入大於 0", page)


if __name__ == "__main__":
    unittest.main()

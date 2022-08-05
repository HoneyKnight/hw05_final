from django.test import Client, TestCase


class CoreTests(TestCase):
    def setUp(self):
        self.guest_client = Client()

    def test_pages_uses_correct_templates(self):
        """Страница 404 используют корректный шаблон"""
        response = self.guest_client.get('/unexisting_page/')
        self.assertTemplateUsed(response, 'core/404.html')

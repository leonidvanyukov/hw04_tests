from http import HTTPStatus

from django.test import TestCase


class ViewTestClass(TestCase):
    def test_error_page(self):
        """Проверка использования кастомного шаблона 404 ошибки"""
        template = 'core/404.html'
        response = self.client.get('/nonexist-page/')
        self.assertTemplateUsed(
                    response,
                    template,
                    f'response = {response}, template = {template}'
                )
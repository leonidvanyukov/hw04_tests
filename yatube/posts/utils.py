from django.conf import settings
from django.core.paginator import Paginator


def create_paginator(obj_list, page):
    paginator = Paginator(obj_list, settings.AMOUNT)
    page_obj = paginator.get_page(page)

    return page_obj


def count_elements(obj_list):
    paginator = Paginator(obj_list, settings.AMOUNT)
    count = paginator.count

    return count

from rest_framework.pagination import PageNumberPagination


class StandardPagination(PageNumberPagination):
    """{count, next, previous, results}; ?page=&page_size= (max 48)."""

    page_size = 12
    page_size_query_param = "page_size"
    max_page_size = 48

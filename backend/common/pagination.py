from rest_framework.pagination import PageNumberPagination


class DefaultPagination(PageNumberPagination):
    """Page-number pagination for every list endpoint (SENTRA_BUILD_SPEC.md §4):
    25/page by default, client may request up to 100 via ``?page_size=``."""

    page_size = 25
    page_size_query_param = "page_size"
    max_page_size = 100

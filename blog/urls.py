from django.urls import path

from . import views

app_name = "blog"

urlpatterns = [
    # Homepage
    path("", views.home, name="home"),

    # Search
    path("search/", views.search, name="search"),

    # Newsletter
    path("newsletter/subscribe/", views.newsletter_subscribe, name="newsletter_subscribe"),
    path("subscribed/", views.subscribed, name="subscribed"),

    # Informational / legal pages
    path("about/", views.about, name="about"),
    path("contact/", views.contact, name="contact"),
    path("privacy/", views.privacy, name="privacy"),
    path("terms/", views.terms, name="terms"),
    path("disclaimer/", views.disclaimer, name="disclaimer"),
    path("affiliate-disclosure/", views.affiliate_disclosure, name="affiliate_disclosure"),

    # Archives
    path("categories/", views.category_index, name="category_index"),
    path("category/<slug:slug>/", views.category_detail, name="category"),
    path("tag/<slug:slug>/", views.tag_detail, name="tag"),
    path("author/<slug:slug>/", views.author_detail, name="author"),

    # Post detail — greedy catch-all, MUST stay last.
    # Matches /<category-slug>/<post-slug>/
    path("<slug:category>/<slug:slug>/", views.post_detail, name="post_detail"),
]

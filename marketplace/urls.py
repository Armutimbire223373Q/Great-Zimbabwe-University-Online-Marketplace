from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('listing/<int:pk>/', views.listing_detail, name='listing_detail'),
    path('listing/create/', views.create_listing, name='create_listing'),
    path('listing/<int:pk>/edit/', views.edit_listing, name='edit_listing'),
    path('listing/<int:pk>/delete/', views.delete_listing, name='delete_listing'),
    path('seller/<int:seller_id>/', views.seller_listings, name='seller_listings'),
    path('favorite/add/<int:pk>/', views.add_favorite, name='add_favorite'),
    path('favorite/remove/<int:pk>/', views.remove_favorite, name='remove_favorite'),
    path('favorites/', views.favorite_listings, name='favorite_listings'),
    path('cart/add/<int:pk>/', views.add_to_cart, name='add_to_cart'),
    path('cart/remove/<int:pk>/', views.remove_from_cart, name='remove_from_cart'),
    path('cart/', views.view_cart, name='view_cart'),
    path('checkout/', views.checkout, name='checkout'),
    path('listing/<int:pk>/report/', views.report_listing, name='report_listing'),
    path('user/<int:user_id>/report/', views.report_user, name='report_user'),
    path('listing/<int:pk>/offer/', views.make_offer, name='make_offer'),
    path('listing/<int:pk>/confirm_deal/', views.confirm_deal, name='confirm_deal'),
    path('listing/<int:pk>/mark/<str:status>/', views.mark_listing_status, name='mark_listing_status'),
    path('events-gigs/', views.browse_events_gigs, name='browse_events_gigs'),
    path('events-gigs/post/', views.post_event_gig, name='post_event_gig'),
    path('store/<str:username>/', views.store, name='store'),
    path('notifications/', views.notifications, name='notifications'),
] 
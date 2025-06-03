from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views, api_views

router = DefaultRouter()
router.register(r'categories', api_views.CategoryViewSet)
router.register(r'listings', api_views.ListingViewSet)
router.register(r'cart', api_views.CartViewSet, basename='cart')
router.register(r'purchases', api_views.PurchaseViewSet, basename='purchase')
router.register(r'reviews', api_views.ReviewViewSet, basename='review')

app_name = 'marketplace'

urlpatterns = [
    # API URLs
    path('api/', include(router.urls)),
    path('api/auth/', include('rest_framework.urls')),
    
    # Web URLs
    path('', views.home, name='home'),
    path('listings/', views.listings, name='listings'),
    path('listings/<int:pk>/', views.listing_detail, name='listing_detail'),
    path('listings/create/', views.create_listing, name='create_listing'),
    path('listings/<int:pk>/edit/', views.edit_listing, name='edit_listing'),
    path('listings/<int:pk>/delete/', views.delete_listing, name='delete_listing'),
    path('listings/<int:pk>/purchase/', views.purchase_listing, name='purchase_listing'),
    path('listings/<int:pk>/swap/', views.swap_listing, name='swap_listing'),
    path('listings/<int:pk>/delivery/', views.delivery_detail, name='delivery_detail'),
    path('listings/<int:pk>/service/', views.service_detail, name='service_detail'),
    path('listings/<int:pk>/swap-detail/', views.swap_detail, name='swap_detail'),
    path('listings/<int:pk>/report/', views.report_listing, name='report_listing'),
    path('listings/<int:pk>/favorite/', views.add_favorite, name='add_favorite'),
    path('listings/<int:pk>/unfavorite/', views.remove_favorite, name='remove_favorite'),
    path('listings/<int:pk>/offer/', views.make_offer, name='make_offer'),
    path('listings/<int:pk>/confirm-deal/', views.confirm_deal, name='confirm_deal'),
    path('listings/<int:pk>/mark/<str:status>/', views.mark_listing_status, name='mark_listing_status'),
    
    # Cart URLs
    path('cart/', views.cart, name='cart'),
    path('cart/add/<int:listing_id>/', views.add_to_cart, name='add_to_cart'),
    path('cart/remove/<int:item_id>/', views.remove_from_cart, name='remove_from_cart'),
    path('cart/clear/', views.clear_cart, name='clear_cart'),
    path('cart/update/<int:listing_id>/', views.update_cart_quantity, name='update_cart_quantity'),
    path('checkout/', views.checkout, name='checkout'),
    
    # Purchase URLs
    path('purchases/', views.purchase_list, name='purchase_list'),
    path('purchases/<int:pk>/', views.purchase_detail, name='purchase_detail'),
    path('purchases/<int:pk>/cancel/', views.cancel_purchase, name='purchase_cancel'),
    path('purchases/<int:pk>/complete/', views.complete_purchase, name='purchase_complete'),
    path('purchases/<int:pk>/rate/', views.rate_user, name='rate_user'),
    
    # User URLs
    path('seller/<int:seller_id>/', views.seller_listings, name='seller_listings'),
    path('store/<str:username>/', views.store, name='store'),
    path('user/<int:user_id>/report/', views.report_user, name='report_user'),
    path('my-listings/', views.my_listings, name='my_listings'),
    path('orders/', views.orders, name='orders'),
    path('favorites/', views.favorite_listings, name='favorite_listings'),
    
    # Event and Gig URLs
    path('events-gigs/', views.browse_events_gigs, name='browse_events_gigs'),
    path('events-gigs/post/', views.post_event_gig, name='post_event_gig'),
    
    # Search
    path('search/', views.search, name='search'),

    # Review URLs
    path('reviews/', views.review_list, name='review_list'),
    path('reviews/create/<int:listing_id>/', views.review_create, name='review_create'),
    path('reviews/<int:pk>/', views.review_detail, name='review_detail'),
    path('reviews/<int:pk>/edit/', views.edit_review, name='review_edit'),
    path('reviews/<int:pk>/delete/', views.delete_review, name='review_delete'),

    # Category URLs
    path('categories/', views.categories, name='categories'),
    path('categories/<int:pk>/', views.category_detail, name='category_detail'),

    # Chat URLs
    path('chat/<int:user_id>/', views.chat_room, name='chat_room'),
    path('chat/<int:user_id>/send/', views.send_message, name='send_message'),

    # Payment URLs
    path('payment/methods/', views.payment_methods, name='payment_methods'),
    path('payment/methods/add/', views.add_payment_method, name='add_payment_method'),
    path('payment/methods/<int:pk>/delete/', views.delete_payment_method, name='delete_payment_method'),
] 
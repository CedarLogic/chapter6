from django.conf.urls import patterns, url, include
from recommender import views

urlpatterns = patterns('',
	url(r'^hello/', views.hello, name='hello'),
	url(r'^chart/', views.chart, name='chart'),
	url(r'^associarules/', views.item_support, name='item_support'),
	url(r'^itemsets/', views.itemsets_support, name='itemsets_support'),
	url(r'^trans/', views.get_all_transactions, name='get_all_transactions')
)
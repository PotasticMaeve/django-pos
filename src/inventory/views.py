from rest_framework.views import APIView
from rest_framework.response import Response
from src.utils.response import GeneralResponse
from .models import Product
from .serializers import ProductSerializer
from rest_framework import status
from django.core.cache import cache
from django.db import transaction

class ProductAPIView(APIView, GeneralResponse):
    def list(self, request):
        search = request.GET.get('search')
        rate_limit_key = f'product_rate_limit_{search}'
        get_cache_rate_limit = cache.get(rate_limit_key)
        
        if get_cache_rate_limit:
            if get_cache_rate_limit >= 3:
                data = self.error(message='rate limited')
                return Response(data)
            cache.set(rate_limit_key, get_cache_rate_limit+1,160)
        else:
            cache.set(rate_limit_key, 1, 160)
            
        cache_key = f'product_cache_{search}'  
        get_cache = cache.get(cache_key)
        
        if get_cache:
            data = self.success(data=get_cache, message='Products cache', is_cache=True)
            return data 
        
        products = Product.objects.filter(is_deleted=False)
        serializer = ProductSerializer(products, many=True)
        data = self.success(data=serializer.data, message='Products retrieved successfully')
        return Response(data)
    
    def retrieve(self, request, id):
        if not isinstance(id, int):
            data = self.error(message='Invalid product ID')
            return Response(data, status=status.HTTP_400_BAD_REQUEST)
        
        product = Product.objects.filter(id=id, is_deleted=False).first()
        if not product:
            data = self.error(message='Product not found')
            return Response(data, status=status.HTTP_404_NOT_FOUND)

        serializer = ProductSerializer(product)
        data = self.success(data=serializer.data, message='Product retrieved successfully')
        return Response(data)
    
    def get(self, request):
        product_id = request.GET.get('id')
        if product_id:
            return self.retrieve(request, product_id)
        return self.list(request)
    
    def post(self, request):
        sid = transaction.savepoint()
        serializer = ProductSerializer(data=request.data)
        if not serializer.is_valid():
            data = self.error(message=serializer.errors)
            transaction.savepoint_rollback(sid)
            return Response(data, status=status.HTTP_400_BAD_REQUEST)
        
        serializer.save()
        data = self.success(data=serializer.data, message='Product created successfully')
        transaction.savepoint_commit(sid)
        return Response(data, status=status.HTTP_201_CREATED)

    def update_data(self, payload, id):
        sid = transaction.savepoint()     
        if not id:
            return False, 'id cannot be empty'
        
        product = Product.objects.filter(id=id, is_deleted=False).first()
        if not product:
            transaction.savepoint_rollback(sid)
            return False, 'product not found'

        serializer = ProductSerializer(product, data=payload, partial=True)
        if not serializer.is_valid():
            transaction.savepoint_rollback(sid)
            return False, serializer.errors

        serializer.save()
        transaction.savepoint_commit(sid)
        return True, serializer.data
    
    def patch(self, request):
        payload = request.data
        id = request.GET.get('id')
        is_success, data = self.update_data(payload, id)
        if not is_success:
            return self.error(message=data)
        
        data = self.success(data=data, message='Product updated successfully')
        return Response(data)
        
    def delete(self, request):
        payload = { 'is_deleted': True }
        id = request.GET.get('id')
        is_success, data = self.update_data(payload, id)
        if not is_success:
            return self.error(message=data)
        
        data = self.success(data=data, message='Product deleted successfully')
        return Response(data)
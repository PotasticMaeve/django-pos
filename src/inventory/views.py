from operator import is_
from rest_framework.views import APIView
from rest_framework.response import Response
from .models import Product
from .serializers import ProductSerializer
from src.utils.response import GeneralResponse

class ProductAPIView(APIView, GeneralResponse):
    def list(self, request):
        products = Product.objects.filter(is_deleted=False)
        serializer = ProductSerializer(products, many=True)
        data = self.success(data=serializer.data, message='Products retrieved successfully')
        return Response(data)
    
    def retrieve(self, request, id):
        if not isinstance(id, int):
            data = self.error(message='Invalid product ID')
            return Response(data, status=400)
        
        product = Product.objects.filter(id=id, is_deleted=False).first()
        if not product:
            data = self.error(message='Product not found')
            return Response(data, status=404)

        serializer = ProductSerializer(product)
        data = self.success(data=serializer.data, message='Product retrieved successfully')
        return Response(data)
    
    def get(self, request):
        product_id = request.GET.get('id')
        if product_id:
            return self.retrieve(request, product_id)
        return self.list(request)
    
    def post(self, request):
        serializer = ProductSerializer(data=request.data)
        if not serializer.is_valid():
            data = self.error(message=serializer.errors)
            return Response(data, status=400)
        
        serializer.save()
        data = self.success(data=serializer.data, message='Product created successfully')
        return Response(data, status=201)

    def patch(self, request, id):
        product = Product.objects.filter(id=id, is_deleted=False).first()
        if not product:
            data = self.error(message='Product not found')
            return Response(data, status=404)

        serializer = ProductSerializer(product, data=request.data, partial=True)
        if not serializer.is_valid():
            data = self.error(message=serializer.errors)
            return Response(data, status=400)

        serializer.save()
        data = self.success(data=serializer.data, message='Product updated successfully')
        return Response(data)
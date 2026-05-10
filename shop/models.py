from django.db import models
from django.utils.text import slugify
from django.urls import reverse
import os

# ==================== دسته‌بندی و برند ====================
class Category(models.Model):
    name = models.CharField(max_length=200, verbose_name="نام دسته")
    slug = models.SlugField(unique=True, allow_unicode=True, verbose_name="اسلاگ")
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='children', verbose_name="دسته والد")
    description = models.TextField(blank=True, verbose_name="توضیحات")
    image = models.ImageField(upload_to='categories/', blank=True, null=True, verbose_name="تصویر دسته")
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "دسته‌بندی"
        verbose_name_plural = "دسته‌بندی‌ها"
        ordering = ['name']
    
    def __str__(self):
        if self.parent:
            return f"{self.parent.name} > {self.name}"
        return self.name
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name, allow_unicode=True)
        super().save(*args, **kwargs)
    
    def get_absolute_url(self):
        return reverse('shop:category_detail', args=[self.slug])

class Brand(models.Model):
    name = models.CharField(max_length=200, verbose_name="نام برند")
    slug = models.SlugField(unique=True, allow_unicode=True)
    logo = models.ImageField(upload_to='brands/', blank=True, null=True)
    description = models.TextField(blank=True)
    
    class Meta:
        verbose_name = "برند"
        verbose_name_plural = "برندها"
    
    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name, allow_unicode=True)
        super().save(*args, **kwargs)

# ==================== کالای اصلی ====================
class Product(models.Model):
    # اطلاعات پایه
    name = models.CharField(max_length=500, verbose_name="نام محصول")
    slug = models.SlugField(unique=True, allow_unicode=True, verbose_name="اسلاگ")
    description = models.TextField(verbose_name="توضیحات کامل")
    short_description = models.CharField(max_length=300, blank=True, verbose_name="توضیحات کوتاه")
    
    # دسته‌بندی و برند
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='products', verbose_name="دسته اصلی")
    brand = models.ForeignKey(Brand, on_delete=models.CASCADE, related_name='products', null=True, blank=True, verbose_name="برند")
    
    # قیمت
    price = models.DecimalField(max_digits=12, decimal_places=2, verbose_name="قیمت اصلی (تومان)")
    discount_price = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True, verbose_name="قیمت با تخفیف")
    
    # آمار
    stock = models.IntegerField(default=0, verbose_name="موجودی کل")
    sold_count = models.IntegerField(default=0, verbose_name="تعداد فروخته شده")
    view_count = models.IntegerField(default=0, verbose_name="تعداد بازدید")
    
    # وضعیت
    is_active = models.BooleanField(default=True, verbose_name="فعال")
    is_featured = models.BooleanField(default=False, verbose_name="ویژه")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "محصول"
        verbose_name_plural = "محصولات"
        ordering = ['-created_at']
    
    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name, allow_unicode=True)
        super().save(*args, **kwargs)
    
    def get_final_price(self):
        """قیمت نهایی با تخفیف"""
        return self.discount_price if self.discount_price else self.price
    
    def get_absolute_url(self):
        return reverse('shop:product_detail', args=[self.slug])

# ==================== ویژگی‌های داینامیک (برای رنگ، سایز و...) ====================
class AttributeName(models.Model):
    """نام ویژگی (مثل: رنگ، سایز، رم، حافظه)"""
    name = models.CharField(max_length=100, verbose_name="نام ویژگی")
    slug = models.SlugField(unique=True, allow_unicode=True)
    
    class Meta:
        verbose_name = "نام ویژگی"
        verbose_name_plural = "نام ویژگی‌ها"
    
    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name, allow_unicode=True)
        super().save(*args, **kwargs)

class AttributeValue(models.Model):
    """مقدار ویژگی (مثل: قرمز، XL، 16GB، 512GB)"""
    attribute = models.ForeignKey(AttributeName, on_delete=models.CASCADE, related_name='values')
    value = models.CharField(max_length=200, verbose_name="مقدار")
    slug = models.SlugField(allow_unicode=True)
    
    class Meta:
        verbose_name = "مقدار ویژگی"
        verbose_name_plural = "مقادیر ویژگی"
        unique_together = ('attribute', 'value')
    
    def __str__(self):
        return f"{self.attribute.name}: {self.value}"
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.value, allow_unicode=True)
        super().save(*args, **kwargs)

class ProductVariant(models.Model):
    """تنوع محصول (مثلاً لپتاپ لنوو با رم 16GB و رنگ مشکی)"""
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='variants')
    attributes = models.ManyToManyField(AttributeValue, related_name='variants', verbose_name="ویژگی‌ها")
    price = models.DecimalField(max_digits=12, decimal_places=2, verbose_name="قیمت این تنوع")
    stock = models.IntegerField(default=0, verbose_name="موجودی این تنوع")
    sku = models.CharField(max_length=100, unique=True, blank=True, verbose_name="کد کالا")
    is_active = models.BooleanField(default=True)
    
    class Meta:
        verbose_name = "تنوع محصول"
        verbose_name_plural = "تنوع محصولات"
    
    def __str__(self):
        attrs = ", ".join([str(av) for av in self.attributes.all()])
        return f"{self.product.name} ({attrs})"
    
    def save(self, *args, **kwargs):
        if not self.sku:
            # ساخت SKU خودکار
            import hashlib
            unique_string = f"{self.product.id}-{self.attributes.all().order_by('id').values_list('id', flat=True)}"
            self.sku = hashlib.md5(unique_string.encode()).hexdigest()[:12].upper()
        super().save(*args, **kwargs)

# ==================== تصاویر محصول با مسیر خودکار ====================
def product_image_upload_path(instance, filename):
    """تعیین مسیر خودکار برای تصاویر بر اساس دسته‌بندی و برند"""
    product = instance.variant.product if instance.variant else instance.product
    category_path = product.category.slug
    
    # مسیر برند اگر وجود داشته باشد
    brand_path = product.brand.slug if product.brand else 'no-brand'
    
    # اسم محصول بدون فاصله
    product_slug = product.slug
    
    return f"products/{category_path}/{brand_path}/{product_slug}/{filename}"

class ProductImage(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='images', null=True, blank=True)
    variant = models.ForeignKey(ProductVariant, on_delete=models.CASCADE, related_name='images', null=True, blank=True)
    image = models.ImageField(upload_to=product_image_upload_path, verbose_name="تصویر")
    alt_text = models.CharField(max_length=200, blank=True, verbose_name="متن جایگزین")
    is_main = models.BooleanField(default=False, verbose_name="تصویر اصلی")
    order = models.PositiveIntegerField(default=0, verbose_name="ترتیب نمایش")
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "تصویر محصول"
        verbose_name_plural = "تصاویر محصولات"
        ordering = ['order', 'created_at']
    
    def __str__(self):
        if self.variant:
            return f"تصویر {self.variant}"
        return f"تصویر {self.product}"
    
    def save(self, *args, **kwargs):
        # اگه این تصویر اصلی هست، بقیه تصاویر اصلی را غیرفعال کن
        if self.is_main:
            if self.variant:
                ProductImage.objects.filter(variant=self.variant, is_main=True).exclude(id=self.id).update(is_main=False)
            else:
                ProductImage.objects.filter(product=self.product, is_main=True).exclude(id=self.id).update(is_main=False)
        super().save(*args, **kwargs)

# ==================== سبد خرید (برای بعد) ====================
class Cart(models.Model):
    user = models.ForeignKey('auth.User', on_delete=models.CASCADE, null=True, blank=True, related_name='carts')
    session_key = models.CharField(max_length=40, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "سبد خرید"
        verbose_name_plural = "سبدهای خرید"
    
    def get_total_price(self):
        total = sum(item.get_total_price() for item in self.items.all())
        return total
    
    def __str__(self):
        if self.user:
            return f"سبد {self.user.username}"
        return f"سبد مهمان {self.session_key}"

class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items')
    variant = models.ForeignKey(ProductVariant, on_delete=models.CASCADE, related_name='cart_items')
    quantity = models.PositiveIntegerField(default=1)
    
    def get_total_price(self):
        return self.variant.price * self.quantity
    
    def __str__(self):
        return f"{self.variant.product.name} x {self.quantity}"
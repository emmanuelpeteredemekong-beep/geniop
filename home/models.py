from django.db import models
from django.contrib.auth.models import User

# Function to calculate price based on number of records in report
# This pricing is for Quick Sales Report feature
def get_price(count):
    if count <= 200:  # If count is 200 or less
        return 500  # Charge 500 naira
    elif count <= 500:  # If count is up to 500
        return 1000  # Charge 1000 naira
    elif count <= 1000:  # If count is up to 1000
        return 1500  # Charge 1500 naira
    elif count <= 2000:  # If count is up to 2000
        return 3000  # Charge 3000 naira
    elif count <= 3500:  # If count is up to 3500
        return 5000  # Charge 5000 naira
    elif count <= 4999:  # If count is up to 4999
        return 7500  # Charge 7500 naira
    else:  # If count is 5000 and above
        return 10000  # Charge 10000 naira

# Model for Home Feed - "What's happening in your market?"
class Post(models.Model):
    # Link this post to the user who created it
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    # Text caption for the market update, can be empty
    caption = models.TextField(blank=True)
    # Optional image uploaded with the post
    image = models.ImageField(upload_to='posts/', blank=True, null=True)
    # Market location, optional
    location = models.CharField(max_length=100, blank=True)
    # Number of sales records, used to calculate price
    count = models.IntegerField(default=0)
    # Price calculated from count using get_price
    price = models.IntegerField(default=0)
    # Time when post was created, auto set
    created_at = models.DateTimeField(auto_now_add=True)

    # Meta settings for this model
    class Meta:
        # Show newest posts first
        ordering = ['-created_at']
        # Nice name in admin panel
        verbose_name = 'Market Post'

    # Override save method to auto calculate price
    def save(self, *args, **kwargs):
        # If count is provided, calculate price
        if self.count:
            self.price = get_price(self.count)
        # Save to database
        super().save(*args, **kwargs)

    # How object shows in admin
    def __str__(self):
        # Show username and first part of caption
        return f"{self.user.username}: {self.caption[:30]}"

# Model for Quick Sales Report calculation
class QuickSalesReport(models.Model):
    # Link to user if logged in, optional
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    # Total sales amount from file
    total_sales = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    # Total expense amount from file
    total_expense = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    # Profit = sales - expense
    profit = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    # Profit margin in percentage
    profit_margin = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    # Number of rows processed
    record_count = models.IntegerField(default=0)
    # Price charged based on count
    price_charged = models.IntegerField(default=0)
    # When report was created
    created_at = models.DateTimeField(auto_now_add=True)
    # Note: We do NOT store uploaded file, only result for privacy

    def __str__(self):
        # Show report id and profit
        return f"Report {self.id} - Profit: {self.profit}"

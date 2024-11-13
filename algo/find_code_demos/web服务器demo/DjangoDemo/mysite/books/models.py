from django.db import models
 
class Book(models.Model):
    title = models.CharField(max_length=200)
    author = models.CharField(max_length=100)
    pub_date = models.DateField()
 
    def __str__(self):
        return self.title
 
    @staticmethod
    def create_sample():
        Book.objects.create(title='Sample Book 1', author='Sample Author', pub_date='2021-01-01')
        Book.objects.create(title='Sample Book 2', author='Sample Author', pub_date='2021-01-01')


class Snippet(models.Model):
    created = models.DateTimeField(auto_now_add=True)
    title = models.CharField(max_length=100, blank=True, default='')
    code = models.TextField()
    linenos = models.BooleanField(default=False)

    class Meta:
        ordering = ['created']
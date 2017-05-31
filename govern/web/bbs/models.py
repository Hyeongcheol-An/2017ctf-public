from django.db import models

class Post(models.Model):
    title = models.CharField(max_length=100)
    content = models.TextField()
    use_script = models.BooleanField()
    author = models.ForeignKey('auth.User')

    class Meta:
        permissions = (
            ('use_script', 'Can insert Javascript into posts'),
        )

    def __str__(self):
        return "Post '{}'".format(self.title)

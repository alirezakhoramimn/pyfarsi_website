import graphene 
from graphene_django import DjangoObjectType
from .models import Category, Article,Comment

class ArticleType(DjangoObjectType):
	class Meta:
		model = Article
		fields = '__all__'
		
	
class Query(graphene.ObjectType):
	all_articles = graphene.List(ArticleType)
	
	
	def resolve_articles(root, info):
		return Article.objects.all()

    def resolve_category_by_name(root, info, name):
        try:
            return Category.objects.get(name=name)
        except Category.DoesNotExist:
            return None

	def resolve_article_by_slug(root,info, slug):
		return Article.objects.filter(slug=slug)
		
		
		


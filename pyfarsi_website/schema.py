from blog import schema as blog_schema 
import graphene 


class Query(graphene.ObjectType, blog_schema.Query):
	pass
	
schema = graphene.Schema(query=Query)

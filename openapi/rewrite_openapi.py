#!/usr/bin/env python3
import yaml
import copy

path = '/home/btoledo/src/btagila/portfolio/openapi/openapi.yaml'
with open(path) as f:
    doc = yaml.safe_load(f)

# Update version
doc['info']['version'] = '0.3.0'

# Update tags
tags = []
for t in doc.get('tags', []):
    name = t.get('name')
    if name in ['categories', 'admin categories']:
        continue
    tags.append(t)
# Add tags
tag_names = [t['name'] for t in tags]
if 'tags' not in tag_names:
    # insert after albums
    new_tags = []
    for t in tags:
        new_tags.append(t)
        if t['name'] == 'albums':
            new_tags.append({'name': 'tags'})
    tags = new_tags
if 'admin tags' not in tag_names:
    new_tags = []
    for t in tags:
        new_tags.append(t)
        if t['name'] == 'admin albums':
            new_tags.append({'name': 'admin tags', 'description': 'Tag management for albums.'})
    tags = new_tags
doc['tags'] = tags

# Remove category paths
paths = doc['paths']
paths_to_remove = []
for p in paths:
    if p.startswith('/api/categories') or p.startswith('/admin/categories'):
        paths_to_remove.append(p)
for p in paths_to_remove:
    paths.pop(p, None)

# Add tag paths
tag_pub_list = {
    'get': {
        'operationId': 'listPublicTags',
        'tags': ['public', 'tags'],
        'summary': 'List published tags',
        'description': 'Published tags only, ordered by weight DESC, name ASC. No pagination. Unpublished tags are never returned.',
        'responses': {
            '200': {
                'description': 'Published tags.',
                'content': {
                    'application/json': {
                        'schema': {
                            'type': 'array',
                            'items': {'$ref': '#/components/schemas/Tag'}
                        }
                    }
                }
            },
            '500': {'$ref': '#/components/responses/Problem'}
        }
    }
}
tag_pub_get = {
    'get': {
        'operationId': 'getPublicTag',
        'tags': ['public', 'tags'],
        'summary': 'Get one published tag',
        'description': 'Draft/unpublished tags read as 404.',
        'parameters': [{
            'name': 'slug',
            'in': 'path',
            'required': True,
            'schema': {'type': 'string', 'pattern': '^[a-z0-9]+(?:-[a-z0-9]+)*$'}
        }],
        'responses': {
            '200': {
                'description': 'The tag.',
                'content': {
                    'application/json': {
                        'schema': {'$ref': '#/components/schemas/Tag'}
                    }
                }
            },
            '404': {'$ref': '#/components/responses/NotFound'},
            '500': {'$ref': '#/components/responses/Problem'}
        }
    }
}
# Insert before /api/albums
new_paths = {}
for k,v in paths.items():
    if k == '/api/albums':
        new_paths['/api/tags'] = tag_pub_list
        new_paths['/api/tags/{slug}'] = tag_pub_get
    new_paths[k] = v
paths = new_paths

admin_tags = {
    'get': {
        'operationId': 'listAdminTags',
        'tags': ['admin tags'],
        'summary': 'List tags',
        'description': 'All tags (including unpublished), ordered by weight DESC, name ASC. Unpublished tags are not assignable from pickers/search.',
        'security': [{'bearerAuth': []}],
        'responses': {
            '200': {'description': 'Tags.', 'content': {'application/json': {'schema': {'type': 'array', 'items': {'$ref': '#/components/schemas/Tag'}}}}},
            '401': {'$ref': '#/components/responses/Unauthorized'},
            '500': {'$ref': '#/components/responses/Problem'}
        }
    },
    'post': {
        'operationId': 'createTag',
        'tags': ['admin tags'],
        'summary': 'Create a tag (inline or from tags page)',
        'description': 'Can be called from the album form for inline creation. Only published/assignable tags may be attached.',
        'security': [{'bearerAuth': []}],
        'requestBody': {'required': True, 'content': {'application/json': {'schema': {'$ref': '#/components/schemas/TagRequest'}}}},
        'responses': {
            '201': {'description': 'Created.', 'content': {'application/json': {'schema': {'$ref': '#/components/schemas/Tag'}}}},
            '400': {'$ref': '#/components/responses/BadRequest'},
            '401': {'$ref': '#/components/responses/Unauthorized'},
            '409': {'description': 'Slug already exists.', 'content': {'application/problem+json': {'schema': {'$ref': '#/components/schemas/ProblemDetail'}}}},
            '500': {'$ref': '#/components/responses/Problem'}
        }
    }
}
admin_tags_order = {
    'put': {
        'operationId': 'reorderTags',
        'tags': ['admin tags'],
        'summary': 'Reorder tags by weight',
        'security': [{'bearerAuth': []}],
        'requestBody': {'required': True, 'content': {'application/json': {'schema': {'$ref': '#/components/schemas/TagOrderRequest'}}}},
        'responses': {
            '200': {'description': 'Ordered.', 'content': {'application/json': {'schema': {'type': 'array', 'items': {'$ref': '#/components/schemas/Tag'}}}}},
            '401': {'$ref': '#/components/responses/Unauthorized'},
            '400': {'$ref': '#/components/responses/BadRequest'},
            '500': {'$ref': '#/components/responses/Problem'}
        }
    }
}
admin_tags_id = {
    'parameters': [{'name': 'id', 'in': 'path', 'required': True, 'schema': {'type': 'string', 'format': 'uuid'}}],
    'get': {
        'operationId': 'getAdminTag',
        'tags': ['admin tags'],
        'summary': 'Get a tag',
        'security': [{'bearerAuth': []}],
        'responses': {
            '200': {'description': 'The tag.', 'content': {'application/json': {'schema': {'$ref': '#/components/schemas/Tag'}}}},
            '401': {'$ref': '#/components/responses/Unauthorized'},
            '404': {'$ref': '#/components/responses/NotFound'}
        }
    },
    'put': {
        'operationId': 'updateTag',
        'tags': ['admin tags'],
        'summary': 'Replace a tag',
        'security': [{'bearerAuth': []}],
        'requestBody': {'required': True, 'content': {'application/json': {'schema': {'$ref': '#/components/schemas/TagRequest'}}}},
        'responses': {
            '200': {'description': 'Updated.', 'content': {'application/json': {'schema': {'$ref': '#/components/schemas/Tag'}}}},
            '400': {'$ref': '#/components/responses/BadRequest'},
            '401': {'$ref': '#/components/responses/Unauthorized'},
            '404': {'$ref': '#/components/responses/NotFound'},
            '409': {'description': 'Slug collision.', 'content': {'application/problem+json': {'schema': {'$ref': '#/components/schemas/ProblemDetail'}}}}
        }
    },
    'delete': {
        'operationId': 'deleteTag',
        'tags': ['admin tags'],
        'summary': 'Delete a tag',
        'description': 'Refused if the tag is still attached to any album.',
        'security': [{'bearerAuth': []}],
        'responses': {
            '204': {'description': 'Deleted.'},
            '401': {'$ref': '#/components/responses/Unauthorized'},
            '404': {'$ref': '#/components/responses/NotFound'},
            '409': {'description': 'Tag still attached to albums.', 'content': {'application/problem+json': {'schema': {'$ref': '#/components/schemas/ProblemDetail'}}}}
        }
    }
}
admin_tags_pub = {
    'parameters': [{'name': 'id', 'in': 'path', 'required': True, 'schema': {'type': 'string', 'format': 'uuid'}}],
    'patch': {
        'operationId': 'setTagPublished',
        'tags': ['admin tags'],
        'summary': 'Publish or unpublish a tag',
        'description': 'Unpublishing hides the tag from public lists and from admin pickers/search; it does not affect album visibility.',
        'security': [{'bearerAuth': []}],
        'requestBody': {'required': True, 'content': {'application/json': {'schema': {'$ref': '#/components/schemas/PublishRequest'}}}},
        'responses': {
            '200': {'description': 'Updated.', 'content': {'application/json': {'schema': {'$ref': '#/components/schemas/Tag'}}}},
            '401': {'$ref': '#/components/responses/Unauthorized'},
            '404': {'$ref': '#/components/responses/NotFound'},
            '500': {'$ref': '#/components/responses/Problem'}
        }
    }
}
new_paths = {}
for k,v in paths.items():
    if k == '/admin/albums':
        new_paths['/admin/tags'] = admin_tags
        new_paths['/admin/tags/order'] = admin_tags_order
        new_paths['/admin/tags/{id}'] = admin_tags_id
        new_paths['/admin/tags/{id}/publish'] = admin_tags_pub
    new_paths[k] = v
paths = new_paths
doc['paths'] = paths

# Update albums
# Public albums
pab = paths.get('/api/albums')
if pab and 'get' in pab:
    op = pab['get']
    op['description'] = 'Published albums only. Each item includes its tags and cover photo. Albums must have at least one tag. When no cover is picked, the cover falls back to the first **published** photo.'
    # replace category param
    params = op.get('parameters', [])
    newp = []
    for pr in params:
        if pr.get('name') == 'category':
            continue
        newp.append(pr)
    newp.insert(0, {
        'name': 'tag',
        'in': 'query',
        'required': False,
        'description': 'Filter by tag slug(s). Multiple values use AND semantics (album must have every specified tag).',
        'schema': {'type': 'array', 'items': {'type': 'string', 'pattern': '^[a-z0-9]+(?:-[a-z0-9]+)*$'}},
        'style': 'form',
        'explode': True
    })
    op['parameters'] = newp

# Admin albums
aab = paths.get('/admin/albums')
if aab and 'get' in aab:
    op = aab['get']
    params = op.get('parameters', [])
    newp = []
    for pr in params:
        if pr.get('name') == 'category':
            continue
        newp.append(pr)
    newp.insert(0, {
        'name': 'tag',
        'in': 'query',
        'required': False,
        'description': 'Filter by tag id(s). Multiple values use AND semantics (album must have every specified tag).',
        'schema': {'type': 'array', 'items': {'type': 'string', 'format': 'uuid'}},
        'style': 'form',
        'explode': True
    })
    op['parameters'] = newp
if aab and 'post' in aab:
    aab['post']['description'] = 'New albums start as drafts unless `published` is set.'
# update album operations
for key in ['/admin/albums/{id}']:
    if key in paths:
        op = paths[key].get('put')
        if op:
            op['description'] = 'Title, description, tags, order, published flag, and cover photo.'
# fix responses
for key in ['/admin/albums']:
    if key in paths and 'post' in paths[key]:
        resp = paths[key]['post'].get('responses', {})
        if '409' in resp:
            resp['409']['description'] = 'A album with this slug already exists.'
for key in ['/admin/albums/{id}']:
    if key in paths and 'put' in paths[key]:
        resp = paths[key]['put'].get('responses', {})
        if '409' in resp:
            resp['409']['description'] = 'Slug collides with a different album.'

# Schemas
schemas = doc['components']['schemas']
# Remove category schemas
schemas.pop('Category', None)
schemas.pop('CategoryRequest', None)
schemas.pop('CategoryId', None)
schemas.pop('CategorySlug', None)
# Add Tag
schemas['Tag'] = {
    'type': 'object',
    'description': 'A reusable label attached to albums (M:N). Unpublished tags are hidden from public lists and from admin pickers/search, but do not affect album visibility.',
    'required': ['id', 'name', 'slug', 'weight', 'published'],
    'properties': {
        'id': {'type': 'string', 'format': 'uuid'},
        'name': {'type': 'string', 'examples': ['Wedding']},
        'slug': {'type': 'string', 'pattern': '^[a-z0-9]+(?:-[a-z0-9]+)*$', 'examples': ['wedding']},
        'weight': {'type': 'integer', 'description': 'Higher weight sorts first. Tiebreaker by name.', 'default': 0},
        'published': {'type': 'boolean'},
        'albumCount': {'type': 'integer', 'description': 'Admin responses only.'}
    },
    'examples': [{'id': '3f6d0a2e-8c1b-4f5a-9d3e-2b7c8e1a4f60', 'name': 'Wedding', 'slug': 'wedding', 'weight': 10, 'published': True, 'albumCount': 2}]
}
# Update Album
if 'Album' in schemas:
    alb = schemas['Album']
    alb['description'] = 'A set of photos — what a visitor opens from the gallery. Albums must have at least one tag.'
    req = alb.get('required', [])
    req = [r for r in req if r not in ['categoryId']]
    if 'tags' not in req:
        req.append('tags')
    alb['required'] = req
    props = alb.get('properties', {})
    props.pop('categoryId', None)
    props.pop('category', None)
    props['tags'] = {
        'type': 'array',
        'minItems': 1,
        'items': {'$ref': '#/components/schemas/Tag'},
        'description': 'Tags attached to the album. Unpublished tags are hidden on public album views; at least one tag must remain attached. Album visibility is independent of tag visibility.'
    }
    alb['properties'] = props
# Update AlbumRequest
if 'AlbumRequest' in schemas:
    ar = schemas['AlbumRequest']
    req = ar.get('required', [])
    req = [r for r in req if r != 'categoryId']
    if 'tagIds' not in req:
        req.append('tagIds')
    ar['required'] = req
    props = ar.get('properties', {})
    props.pop('categoryId', None)
    props['tagIds'] = {
        'type': 'array',
        'minItems': 1,
        'items': {'type': 'string', 'format': 'uuid'},
        'description': 'At least one tag must be attached. Only published/assignable tags may be attached; unpublished tags are not assignable or searchable.'
    }
    ar['properties'] = props
# Add TagRequest, TagOrderRequest
schemas['TagRequest'] = {
    'type': 'object',
    'required': ['name'],
    'properties': {
        'name': {'type': 'string', 'minLength': 1},
        'slug': {'type': 'string', 'pattern': '^[a-z0-9]+(?:-[a-z0-9]+)*$'},
        'weight': {'type': 'integer', 'default': 0},
        'published': {'type': 'boolean', 'default': False}
    }
}
schemas['TagOrderRequest'] = {
    'type': 'object',
    'required': ['items'],
    'properties': {
        'items': {
            'type': 'array',
            'items': {
                'type': 'object',
                'required': ['id', 'weight'],
                'properties': {
                    'id': {'type': 'string', 'format': 'uuid'},
                    'weight': {'type': 'integer'}
                }
            }
        }
    }
}
# Remove params
params = doc['components'].get('parameters', {})
params.pop('CategoryId', None)
params.pop('CategorySlug', None)

doc['paths'] = paths
doc['tags'] = tags

with open(path, 'w') as f:
    yaml.safe_dump(doc, f, sort_keys=False, allow_unicode=True, width=1000)

print('done')

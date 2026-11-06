#!/usr/bin/env python3
import re

path = '/home/btoledo/src/btagila/portfolio/openapi/openapi.yaml'
with open(path) as f:
    s = f.read()

# Bump version
s = s.replace("version: 0.2.0", "version: 0.3.0")

# Remove tags section entries for categories
# tags block
s = re.sub(r'  - name: categories\n', '', s)
s = re.sub(r'  - name: admin categories\n', '', s)
# add tags
if '  - name: tags\n' not in s:
    s = s.replace('  - name: albums\n', '  - name: albums\n  - name: tags\n')
if '  - name: admin tags\n' not in s:
    s = s.replace('  - name: admin albums\n', '  - name: admin albums\n  - name: admin tags\n')

# Remove /api/categories and /api/categories/{slug}
# Remove blocks
s = re.sub(r'  /api/categories:\n.*?(?=^  /api/albums:|\n  /[a-z])', '  /api/categories:\n    # REMOVED\n\n', s, flags=re.S)
s = re.sub(r'  /api/categories/\{slug\}:\n.*?(?=^  /api/|\n  /[a-z])', '  /api/categories/{slug}:\n    # REMOVED\n\n', s, flags=re.S)

# Remove admin categories paths
s = re.sub(r'  /admin/categories:\n.*?(?=^  /admin/[a-z]|\n  /[a-z])', '  /admin/categories:\n    # REMOVED\n\n', s, flags=re.S)
s = re.sub(r'  /admin/categories/order:\n.*?(?=^  /admin/[a-z]|\n  /[a-z])', '  /admin/categories/order:\n    # REMOVED\n\n', s, flags=re.S)
s = re.sub(r'  /admin/categories/\{id\}:\n.*?(?=^  /admin/[a-z]|\n  /[a-z])', '  /admin/categories/{id}:\n    # REMOVED\n\n', s, flags=re.S)
s = re.sub(r'  /admin/categories/\{id\}/publish:\n.*?(?=^  /admin/[a-z]|\n  /[a-z])', '  /admin/categories/{id}/publish:\n    # REMOVED\n\n', s, flags=re.S)

# Remove params
s = re.sub(r'    CategoryId:\n.*?(?=^    [A-Z]|\n  schemas:)', '', s, flags=re.S)
s = re.sub(r'    CategorySlug:\n.*?(?=^    [A-Z]|\n  schemas:)', '', s, flags=re.S)

# Add Tag schema and update Album
# Remove Category schema
s = re.sub(r'    Category:\n.*?(?=^    [A-Z][a-zA-Z0-9_]*:|\n  securitySchemes:)', '', s, flags=re.S)

# Add Tag schema before Album
tag_schema = '''    Tag:
      type: object
      description: A reusable label attached to albums (M:N). Unpublished tags are hidden from public lists and from admin pickers/search, but do not affect album visibility.
      required: [id, name, slug, weight, published]
      properties:
        id:
          type: string
          format: uuid
        name:
          type: string
          examples: ['Wedding']
        slug:
          type: string
          pattern: '^[a-z0-9]+(?:-[a-z0-9]+)*$'
          examples: [wedding]
        weight:
          type: integer
          description: Higher weight sorts first. Tiebreaker by name.
          default: 0
        published:
          type: boolean
        albumCount:
          type: integer
          description: Admin responses only.
      examples:
        - id: 3f6d0a2e-8c1b-4f5a-9d3e-2b7c8e1a4f60
          name: Wedding
          slug: wedding
          weight: 10
          published: true
          albumCount: 2

'''

s = s.replace('    Album:\n', tag_schema + '    Album:\n')

# Update Album schema
# Replace description
s = s.replace('      description: A set of photos — what a visitor opens from the gallery index.\n', 
              '      description: A set of photos — what a visitor opens from the gallery. Albums must have at least one tag.\n')
# Replace required
s = s.replace('      required: [id, categoryId, title, slug, sortOrder, published]\n',
              '      required: [id, title, slug, sortOrder, published, tags]\n')
# Remove categoryId
s = re.sub(r'        categoryId:\n          type: string\n          format: uuid\n', '', s)
# Remove embedded category
s = re.sub(r'        category:\n          allOf:\n            - \$ref: \'#\/components\/schemas\/Category\'\n          description: Embedded so the gallery index renders from one request\.\n', '', s)
# Add tags
s = s.replace('        sortOrder:\n          type: integer\n          minimum: 0\n',
              '        sortOrder:\n          type: integer\n          minimum: 0\n        tags:\n          type: array\n          minItems: 1\n          items:\n            $ref: \'#/components/schemas/Tag\'\n          description: Tags attached to the album. Unpublished tags are hidden on public album views; at least one published-or-assignable tag must remain valid.\n')

# Update AlbumRequest
s = s.replace('      required: [title, categoryId]\n', '      required: [title, tagIds]\n')
s = re.sub(r'        categoryId:\n          type: string\n          format: uuid\n', '', s)
s = s.replace('        title:\n          type: string\n          examples: [\'Spring studio session\']\n',
              '        title:\n          type: string\n          examples: [\'Spring studio session\']\n        tagIds:\n          type: array\n          minItems: 1\n          items:\n            type: string\n            format: uuid\n          description: At least one tag must be attached. Tags must be published/assignable at creation; unpublished tags are not assignable.\n')

# Update listPublicAlbums description
old = '''      description: |
        Published albums only. Each item embeds its category and cover photo so the
        gallery index renders from one request; when no cover is picked, the cover
        falls back to the first **published** photo.'''
new = '''      description: |
        Published albums only. Each item includes its tags and cover photo. Albums must
        have at least one tag. When no cover is picked, the cover falls back to the
        first **published** photo.'''
s = s.replace(old, new)

# Update category param to tag
oldp = '''        - name: category
          in: query
          required: false
          description: Filter by category slug.
          schema:
            type: string
            examples: [family]'''
newp = '''        - name: tag
          in: query
          required: false
          description: Filter by tag slug(s). Multiple values use AND semantics (album must have every specified tag).
          schema:
            type: array
            items:
              type: string
              pattern: '^[a-z0-9]+(?:-[a-z0-9]+)*$'
            examples: [["wedding","outdoor"]]
          style: form
          explode: true'''
s = s.replace(oldp, newp)

with open(path, 'w') as f:
    f.write(s)

print('done')

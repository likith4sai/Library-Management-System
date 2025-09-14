class Book:
    def _init_(self, title, author, isbn):
        self.title = title
        self.author = author
        self.isbn = isbn

    def to_dict(self):
        return {
            'title': self.title,
            'author': self.author,
            'isbn': self.isbn
        }

class Member:
    def _init_(self, name, email, membership_id):
        self.name = name
        self.email = email
        self.membership_id = membership_id

    def to_dict(self):
        return {
            'name': self.name,
            'email': self.email,
            'membership_id': self.membership_id
        }

class User:
    def _init_(self, name, email, password, role='user'):
        self.name = name
        self.email = email
        self.password = password  # In a real app, ensure this is hashed
        self.role = role  # "user" or "librarian"

    def to_dict(self):
        return {
            'name': self.name,
            'email': self.email,
            'role': self.role
        }

    def is_librarian(self):
        return self.role == 'librarian'

    def is_user(self):
        return self.role == 'user'
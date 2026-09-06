"""Business logic layer.

Services own business rules, validation and transaction boundaries.
Repositories (in `app/repositories/`) handle raw ORM access when queries
grow complex; otherwise services query directly.
"""
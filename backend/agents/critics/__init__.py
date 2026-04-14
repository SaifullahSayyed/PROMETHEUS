from . import security, product, compliance, scalability, business
CRITICS = {
    "SECURITY": security.run,
    "PRODUCT": product.run,
    "COMPLIANCE": compliance.run,
    "SCALABILITY": scalability.run,
    "BUSINESS": business.run,
}
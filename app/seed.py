from . import db
from .models import Product

def seed_products():
    
    
    demo = [
        Product(name="Whey Protein 1kg", category="Protein", price=299.00, stock=20, image_file="prot.jpg",
                description="Basic whey protein for recovery."),
        Product(name="Creatine Monohydrate 300g", category="Creatine", price=179.00, stock=15, image_file="creatin.jpg",
                description="Strength and performance support."),
        Product(name="Pre-Workout", category="Energy", price=219.00, stock=10, image_file="PreWork.jpg",
                description="Energy and focus before training."),
        Product(name="Omega-3 Capsules", category="Health", price=129.00, stock=25, image_file="OM3.jpg",
                description="Daily omega-3 supplement."),
        Product(name="Multivitamin", category="Vitamins", price=99.00, stock=30, image_file="Mult.jpg",
                description="General vitamin support."),
        Product(name="Creatine Monohydrate 500g", category="Creatine", price=349.00, stock=15, image_file="creatin.jpg",
                description="Strength and performance support."),
        Product(name="Whey Protein 4kg", category="Protein", price=1199.00, stock=20, image_file="prot4.jpg",
                description="Basic whey protein for recovery."),
        Product(name="Vitamin D-3", category="Vitamins", price=149.00, stock=30, image_file="vitD.jpg",
                description="Daily dose of vitamin D."),
        Product(name="Energi, 90 vegan capsules", category="Energy", price=219.00, stock=10, image_file="energy.jpg",
                description="Energy and focus, for everyday use."),
    ]
    
    # Loop through our demo list to update were needed!
    for p in demo:
        existing = Product.query.filter_by(name=p.name).first()
        
        if not existing:
            db.session.add(p)
        else:
            
            existing.image_file = p.image_file
            existing.category = p.category
            existing.price = p.price
            existing.description = p.description
    db.session.commit()
    
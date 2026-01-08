from core.config import ITEMS_PRICES

def craft_item(villager_state, item_name):
    """
    Tente de crafter un objet.
    Retourne (success, message)
    """
    # Vérification basique des rôles pour le 'lore' (facultatif mais sympa)
    role = villager_state.get('role', '')
    
    # Kael le Forgeron -> Épée
    if item_name == "Épée" and "Forgeron" not in role:
        return False, "Je ne sais pas forger..."
        
    # Elora -> Potion
    if item_name == "Potion" and "Apothicaire" not in role:
        return False, "Je ne sais pas faire de potions..."

    # Succès
    if 'inventory' not in villager_state: villager_state['inventory'] = []
    villager_state['inventory'].append(item_name)
    return True, f"J'ai fabriqué : {item_name}"

def transaction(buyer_state, seller_state, item_name, seller_name):
    """
    Gère l'achat d'un objet.
    Retourne (success, message)
    """
    if item_name not in seller_state.get('inventory', []):
        return False, f"{seller_name} n'a pas de {item_name} !"

    price = ITEMS_PRICES.get(item_name, 10)
    
    if buyer_state['gold'] < price:
        return False, f"Pas assez d'or ({buyer_state['gold']}/{price})"

    # Transaction
    buyer_state['gold'] -= price
    seller_state['gold'] += price
    
    seller_state['inventory'].remove(item_name)
    if 'inventory' not in buyer_state: buyer_state['inventory'] = []
    buyer_state['inventory'].append(item_name)
    
    return True, f"Acheté {item_name} à {seller_name} pour {price} or"

# apenas pra indicar no modelo qual os tipos
numero: int = 0
boolean: bool = False
string: str = ''

# O que tem 1: {...} significa que pdoerá ter mais dicts adicionados
# naquele conjunto, seguindo como 2: {...}, 3: {...} e etc

modelo = {
    'class': string,
    'level': numero,
    'origin': string,
    'race': string,
    'subrace': string,
    'alignment': string,
    'inspiration': boolean,
    'proeficiencie_bonus': numero,
    'CA': numero,
    'initiative': numero,
    'movement_speed': string,
    'total_hp': numero,
    'current_hp': numero,
    'temp_hp': numero,
    'hp_dice_sides': numero,
    'total_hp_dices': numero,
    'current_hp_dices': numero,
    'personality_traits': string,
    'ideals': string,
    'bonds': string,
    'flaws': string,
    'passive_wisdom': numero,
    'death_saving_throws': {
        'success': numero,
        'fails': numero,
    },
    'customizable_feature': {
        1: {
            'name': string,
            'total': numero,
            'current_value': numero
        },
    },
    'tool_proeficiences': {
        1: {
            'name': string,
            'proeficience_level': string,
            'atribute': string,
            'mods': numero,
        },
    },
    'other_proeficience': {
        1: {
            'type': string,
            'proeficience_description': string,
        },
    },
    'atributes': {
        'for': {'value': numero, 'mod': numero},
        'des': {'value': numero, 'mod': numero},
        'con': {'value': numero, 'mod': numero},
        'int': {'value': numero, 'mod': numero},
        'sab': {'value': numero, 'mod': numero},
        'car': {'value': numero, 'mod': numero},
    },
    'saving_throws': {
        'for': {
            'default_value': numero,
            'total_value': numero,
            'is_proeficient': boolean
        },
        'des': {
            'default_value': numero,
            'total_value': numero,
            'is_proeficient': boolean
        },
        'con': {
            'default_value': numero,
            'total_value': numero,
            'is_proeficient': boolean
        },
        'int': {
            'default_value': numero,
            'total_value': numero,
            'is_proeficient': boolean
        },
        'sab': {
            'default_value': numero,
            'total_value': numero,
            'is_proeficient': boolean
        },
        'car': {
            'default_value': numero,
            'total_value': numero,
            'is_proeficient': boolean
        },
    },
    'attacks': {
        1: {
            'name': string,
            'roll': {
                'should_roll': boolean,
                'atribute': string,
                'is_proeficient': boolean,
                'mods': numero,
            },
            'range': string,
            'magic_bonus': numero,
            'critical_margin': numero,
            'damage': {
                1: {
                  'dices': string,
                  'atribute': string,
                  'mods': numero,
                  'type': string,
                  'critical_damage_dices': string,
                },
            },
            'save_throw': {
                'require_save': boolean,
                'atribute': string,
                'CD': string,
                'effect': string,
            },
            'description': string,
        },
    },
    'inventory': {
        'money': {
            'total_sum': numero,
            'total_weight': numero,
            'pc': numero,
            'pp': numero,
            'pe': numero,
            'po': numero,
            'pl': numero,
        },
        1: {
            'name': string,
            'quantity': numero,
            'weight': numero,
        }
    },
    'skills': {
        1: {
            'name': string,
            'from': string,
            'description':  string,
        },
    },
    'bio': {
        'age': numero,
        'size': string,
        'height': numero,
        'weight': numero,
    }
}

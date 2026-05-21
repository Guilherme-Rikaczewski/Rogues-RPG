from pydantic import BaseModel
import enum


class Atributte(str, enum.Enum):
    str = 'str'
    dex = 'dex'
    con = 'con'
    int = 'int'
    wis = 'wis'
    cha = 'cha'


class DeathSavingThrows(BaseModel):
    success: int = 0
    fails: int = 0


class CustomizableFeature(BaseModel):
    name: str | None = None
    total: int | None = None
    current_value: int | None = None


class ToolProficiencie(BaseModel):
    name: str | None = None
    proficiencies_level: str | None = None
    attribute: Atributte | None = None
    mods: int | None = None


class OtherProficiencie(BaseModel):
    type: str | None = None
    proficiency_description:  str | None = None


class AttributeSpecs(BaseModel):
    value: int = 10
    mod: int = 0


class CharAttributes(BaseModel):
    str: AttributeSpecs
    dex: AttributeSpecs
    con: AttributeSpecs
    int: AttributeSpecs
    wis: AttributeSpecs
    cha: AttributeSpecs


class SavingThrowSpecs(BaseModel):
    default_value: int
    total_value: int
    is_proficient: bool = False


class SavingThrows(BaseModel):
    str: SavingThrowSpecs
    dex: SavingThrowSpecs
    con: SavingThrowSpecs
    int: SavingThrowSpecs
    wis: SavingThrowSpecs
    cha: SavingThrowSpecs


class AttackRoll(BaseModel):
    should_roll: bool = True
    attribute: Atributte | None = None
    is_proficient: bool = True
    mods: int = 0


class Damage(BaseModel):
    dices: str | None = None
    attribute: Atributte | None = None
    mods: int = 0
    type: str | None = None
    critical_damage_dices: str | None = None


class SaveThrow(BaseModel):
    require_save: bool = False
    attribute: Atributte | None = None
    DC: str | None = None
    effect: str | None = None


class Attack(BaseModel):
    name: str | None = None
    roll: AttackRoll
    range: str | None = None
    magic_bonus: int = 0
    critical_margin: int = 20
    damage: list[Damage] = [Damage()]
    save_throw: SaveThrow
    description: str | None = None


class Money(BaseModel):
    total_weight: float = 0
    cp: int = 0
    sp: int = 0
    ep: int = 0
    gp: int = 0
    pp: int = 0


class Item(BaseModel):
    name: str | None = None
    quantity: int = 0
    weight: float | None = 0


class Inventory(BaseModel):
    money: Money
    items: list[Item] = []


class Trait(BaseModel):
    name: str | None = None
    from_origin: str | None = None
    description: str | None = None


class Bio(BaseModel):
    age: str | None = None
    size: str | None = None
    height: str | None = None
    weight: str | None = None
    appearance: str | None = None
    allies: str | None = None
    backstory: str | None = None
    treasure: str | None = None


class SpellComponents(BaseModel):
    V: bool = False
    S: bool = False
    M: bool = False


class SpellAttack(BaseModel):
    is_an_attack: bool = False
    damage: list[Damage] = [Damage()]
    healing: str | None = None
    save_throw: SaveThrow
    add_attribute_mod_on_damage_or_heal: bool = False
    description: str | None = None
    from_class: str | None = None


class Spell(BaseModel):
    level: int
    name: str | None = None
    school: str | None = None
    ritual: bool = False
    cast_time: str | None = None
    range: str | None = None
    target: str | None = None
    components: SpellComponents
    concentration: bool = False
    duration: str | None = None
    cast_attribute: Atributte | None = None
    innate: bool = False
    attack: SpellAttack


class SlotSpec(BaseModel):
    value: int = 0
    mod: int = 0


class SpellSlots(BaseModel):
    level_1: SlotSpec
    level_2: SlotSpec
    level_3: SlotSpec
    level_4: SlotSpec
    level_5: SlotSpec
    level_6: SlotSpec
    level_7: SlotSpec
    level_8: SlotSpec
    level_9: SlotSpec


class SkillSpecs(BaseModel):
    atribute: Atributte
    proficiency_level: str | None = None
    jack_of_all_trades_on: bool = False
    reliable_talent_on: bool = False
    other_mod: int = 0
    total: int | None = None


class Skills(BaseModel):
    acrobatics: SkillSpecs = SkillSpecs(atribute=Atributte.dex)
    animal_handing: SkillSpecs = SkillSpecs(atribute=Atributte.dex)
    arcana: SkillSpecs = SkillSpecs(atribute=Atributte.dex)
    athletics: SkillSpecs = SkillSpecs(atribute=Atributte.dex)
    deception: SkillSpecs = SkillSpecs(atribute=Atributte.dex)
    history: SkillSpecs = SkillSpecs(atribute=Atributte.dex)
    insight: SkillSpecs = SkillSpecs(atribute=Atributte.dex)
    intimidation: SkillSpecs = SkillSpecs(atribute=Atributte.dex)
    investigation: SkillSpecs = SkillSpecs(atribute=Atributte.dex)
    medicine: SkillSpecs = SkillSpecs(atribute=Atributte.dex)
    nature: SkillSpecs = SkillSpecs(atribute=Atributte.dex)
    perception: SkillSpecs = SkillSpecs(atribute=Atributte.dex)
    performance: SkillSpecs = SkillSpecs(atribute=Atributte.dex)
    persuasion: SkillSpecs = SkillSpecs(atribute=Atributte.dex)
    religion: SkillSpecs = SkillSpecs(atribute=Atributte.dex)
    sleight_of_hand: SkillSpecs = SkillSpecs(atribute=Atributte.dex)
    stealth: SkillSpecs = SkillSpecs(atribute=Atributte.dex)
    survival: SkillSpecs = SkillSpecs(atribute=Atributte.dex)

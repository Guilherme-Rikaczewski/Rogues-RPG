from pydantic import BaseModel, Field
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
    str: AttributeSpecs = Field(
        default_factory=lambda: AttributeSpecs()
    )
    dex: AttributeSpecs = Field(
        default_factory=lambda: AttributeSpecs()
    )
    con: AttributeSpecs = Field(
        default_factory=lambda: AttributeSpecs()
    )
    int: AttributeSpecs = Field(
        default_factory=lambda: AttributeSpecs()
    )
    wis: AttributeSpecs = Field(
        default_factory=lambda: AttributeSpecs()
    )
    cha: AttributeSpecs = Field(
        default_factory=lambda: AttributeSpecs()
    )


class SavingThrowSpecs(BaseModel):
    default_value: int = 0
    total_value: int = 0
    is_proficient: bool = False


class SavingThrows(BaseModel):
    str: SavingThrowSpecs = Field(
        default_factory=lambda: SavingThrowSpecs()
    )
    dex: SavingThrowSpecs = Field(
        default_factory=lambda: SavingThrowSpecs()
    )
    con: SavingThrowSpecs = Field(
        default_factory=lambda: SavingThrowSpecs()
    )
    int: SavingThrowSpecs = Field(
        default_factory=lambda: SavingThrowSpecs()
    )
    wis: SavingThrowSpecs = Field(
        default_factory=lambda: SavingThrowSpecs()
    )
    cha: SavingThrowSpecs = Field(
        default_factory=lambda: SavingThrowSpecs()
    )


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
    roll: AttackRoll = Field(
        default_factory=lambda: AttackRoll()
    )
    range: str | None = None
    magic_bonus: int = 0
    critical_margin: int = 20
    damage: list[Damage] = Field(
        default_factory=lambda: [Damage()]
    )
    save_throw: SaveThrow = Field(
        default_factory=lambda: SaveThrow()
    )
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
    money: Money = Field(
        default_factory=lambda: Money()
    )
    items: list[Item] = Field(
        default_factory=list
    )


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
    damage: list[Damage] = Field(
        default_factory=lambda: [Damage()]
    )
    healing: str | None = None
    save_throw: SaveThrow = Field(
        default_factory=lambda: SaveThrow()
    )
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
    attack: SpellAttack = Field(
        default_factory=lambda: SpellAttack()
    )


class SlotSpec(BaseModel):
    value: int = 0
    mod: int = 0


class SpellSlots(BaseModel):
    level_1: SlotSpec = Field(
        default_factory=lambda: SlotSpec()
    )
    level_2: SlotSpec = Field(
        default_factory=lambda: SlotSpec()
    )
    level_3: SlotSpec = Field(
        default_factory=lambda: SlotSpec()
    )
    level_4: SlotSpec = Field(
        default_factory=lambda: SlotSpec()
    )
    level_5: SlotSpec = Field(
        default_factory=lambda: SlotSpec()
    )
    level_6: SlotSpec = Field(
        default_factory=lambda: SlotSpec()
    )
    level_7: SlotSpec = Field(
        default_factory=lambda: SlotSpec()
    )
    level_8: SlotSpec = Field(
        default_factory=lambda: SlotSpec()
    )
    level_9: SlotSpec = Field(
        default_factory=lambda: SlotSpec()
    )


class SkillSpecs(BaseModel):
    atribute: Atributte
    proficiency_level: str | None = None
    jack_of_all_trades_on: bool = False
    reliable_talent_on: bool = False
    other_mod: int = 0
    total: int | None = None


class Skills(BaseModel):
    acrobatics: SkillSpecs = Field(
        default_factory=lambda: SkillSpecs(atribute=Atributte.dex)
    )
    animal_handing: SkillSpecs = Field(
        default_factory=lambda: SkillSpecs(atribute=Atributte.wis)
    )
    arcana: SkillSpecs = Field(
        default_factory=lambda: SkillSpecs(atribute=Atributte.int)
    )
    athletics: SkillSpecs = Field(
        default_factory=lambda: SkillSpecs(atribute=Atributte.str)
    )
    deception: SkillSpecs = Field(
        default_factory=lambda: SkillSpecs(atribute=Atributte.cha)
    )
    history: SkillSpecs = Field(
        default_factory=lambda: SkillSpecs(atribute=Atributte.int)
    )
    insight: SkillSpecs = Field(
        default_factory=lambda: SkillSpecs(atribute=Atributte.wis)
    )
    intimidation: SkillSpecs = Field(
        default_factory=lambda: SkillSpecs(atribute=Atributte.cha)
    )
    investigation: SkillSpecs = Field(
        default_factory=lambda: SkillSpecs(atribute=Atributte.int)
    )
    medicine: SkillSpecs = Field(
        default_factory=lambda: SkillSpecs(atribute=Atributte.wis)
    )
    nature: SkillSpecs = Field(
        default_factory=lambda: SkillSpecs(atribute=Atributte.int)
    )
    perception: SkillSpecs = Field(
        default_factory=lambda: SkillSpecs(atribute=Atributte.wis)
    )
    performance: SkillSpecs = Field(
        default_factory=lambda: SkillSpecs(atribute=Atributte.cha)
    )
    persuasion: SkillSpecs = Field(
        default_factory=lambda: SkillSpecs(atribute=Atributte.cha)
    )
    religion: SkillSpecs = Field(
        default_factory=lambda: SkillSpecs(atribute=Atributte.int)
    )
    sleight_of_hand: SkillSpecs = Field(
        default_factory=lambda: SkillSpecs(atribute=Atributte.dex)
    )
    stealth: SkillSpecs = Field(
        default_factory=lambda: SkillSpecs(atribute=Atributte.dex)
    )
    survival: SkillSpecs = SkillSpecs(atribute=Atributte.wis)

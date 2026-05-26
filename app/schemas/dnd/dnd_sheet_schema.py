from pydantic import BaseModel
import dnd_types as dt


class DnDSheet(BaseModel):
    schema_version: int

    char_class: str | None = None
    level: int = 1
    origin: str | None = None
    race: str | None = None
    subrace: str | None = None
    alignment: str | None = None
    inspiration: bool = False
    proficiency_bonus: int = 2
    armor_class: int | None = None
    initiative: int | None = None
    movement_speed: str | None = None
    total_hp: int | None = None
    current_hp: int | None = None
    temp_hp: int | None = None
    hp_dice_sides: int | None = None
    total_hp_dices: int | None = None
    current_hp_dices: int | None = None
    personality_traits: str | None = None
    ideals: str | None = None
    bonds: str | None = None
    flaws: str | None = None
    passive_perception: int | None = None
    passive_perception_mod: int = 0

    spell_save_dc: int | None = None
    spell_attack_bonus: int | None = None
    spellcasting_attribute: dt.Atributte | None = None

    death_saving_throws: dt.DeathSavingThrows
    attributes: dt.CharAttributes
    saving_throws: dt.SavingThrows
    inventory: dt.Inventory
    bio: dt.Bio
    skills: dt.Skills
    spell_slots: dt.SpellSlots

    customizable_features: list[dt.CustomizableFeature] = []
    tool_proficiencies: list[dt.ToolProficiencie] = []
    other_proficiencies: list[dt.OtherProficiencie] = []
    attacks: list[dt.Attack] = []
    traits: list[dt.Trait] = []
    spells: list[dt.Spell] = []

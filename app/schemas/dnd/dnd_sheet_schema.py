from pydantic import BaseModel, Field
from app.schemas.types import make_partial
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

    customizable_features: list[dt.CustomizableFeature] = Field(
        default_factory=list
    )
    tool_proficiencies: list[dt.ToolProficiencie] = Field(default_factory=list)
    other_proficiencies: list[dt.OtherProficiencie] = Field(
        default_factory=list
        )
    attacks: list[dt.Attack] = Field(default_factory=list)
    traits: list[dt.Trait] = Field(default_factory=list)
    spells: list[dt.Spell] = Field(default_factory=list)


DnDSheetUpdate = make_partial(DnDSheet)

from pydantic import (
    StringConstraints,
    AfterValidator,
    create_model,
    BaseModel
)
from typing import (
    Any,
    Annotated,
    Union,
    get_args,
    get_origin,
)


def validate_password(password: str) -> str:
    if not any(char.islower() for char in password):
        raise ValueError("Password must contain a lowercase letter")

    if not any(char.isupper() for char in password):
        raise ValueError("Password must contain an uppercase letter")

    if not any(char.isdigit() for char in password):
        raise ValueError("Password must contain a number")

    return password


_partial_cache: dict[type[BaseModel], type[BaseModel]] = {}


def _make_partial_annotation(annotation: Any) -> Any:

    origin = get_origin(annotation)

    # list[T]
    if origin is list:
        item_type = get_args(annotation)[0]

        if (
            isinstance(item_type, type)
            and issubclass(item_type, BaseModel)
        ):
            return list[make_partial(item_type)]

        return annotation

    # Union[X, Y]
    if origin is Union:
        args = []

        for arg in get_args(annotation):

            if (
                isinstance(arg, type)
                and issubclass(arg, BaseModel)
            ):
                args.append(make_partial(arg))
            else:
                args.append(arg)

        return Union[tuple(args)]

    # BaseModel
    if (
        isinstance(annotation, type)
        and issubclass(annotation, BaseModel)
    ):
        return make_partial(annotation)

    return annotation


def make_partial(model: type[BaseModel]) -> type[BaseModel]:

    if model in _partial_cache:
        return _partial_cache[model]

    partial_name = f"{model.__name__}Update"

    # placeholder para suportar recursão
    partial_model = create_model(partial_name)

    _partial_cache[model] = partial_model

    fields = {}

    for field_name, field in model.model_fields.items():

        annotation = _make_partial_annotation(
            field.annotation
        )

        fields[field_name] = (
            annotation | None,
            None
        )

    partial_model = create_model(
        partial_name,
        **fields
    )

    _partial_cache[model] = partial_model

    return partial_model


Username = Annotated[
    str,
    StringConstraints(
        max_length=20,
        min_length=1,
        strip_whitespace=True,
    )
]

Password = Annotated[
    str,
    StringConstraints(
        min_length=8,
        max_length=50,
        strip_whitespace=True,
    ),
    AfterValidator(validate_password)
]

RoomName = Annotated[
    str,
    StringConstraints(
        max_length=100,
        min_length=1,
        strip_whitespace=True,
    )
]

RoomCode = Annotated[
    str,
    StringConstraints(
        max_length=6,
        min_length=6,
        strip_whitespace=True,
        to_upper=True,
    )
]

ColorHexCode = Annotated[
    str,
    StringConstraints(
        max_length=7,
        min_length=7,
        strip_whitespace=True,
    )
]

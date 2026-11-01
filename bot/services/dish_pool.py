from dataclasses import dataclass


@dataclass(frozen=True)
class PoolDish:
    name: str   # как показываем пользователю
    wiki: str   # точное название статьи в английской Википедии
    query: str  # поисковый запрос в TheMealDB (фото и рецепт)


DISH_POOL = [
    PoolDish("Пицца", "Pizza", "Pizza"),
    PoolDish("Суши", "Sushi", "Sushi"),
    PoolDish("Лазанья", "Lasagna", "Lasagne"),
    PoolDish("Мусака", "Moussaka", "Moussaka"),
    PoolDish("Паэлья", "Paella", "Paella"),
    PoolDish("Рамен", "Ramen", "Ramen"),
    PoolDish("Тако", "Taco", "Taco"),
    PoolDish("Буррито", "Burrito", "Burrito"),
    PoolDish("Гамбургер", "Hamburger", "Burger"),
    PoolDish("Блины", "Pancake", "Pancakes"),
    PoolDish("Брауни", "Chocolate brownie", "Brownie"),
    PoolDish("Чизкейк", "Cheesecake", "Cheesecake"),
    PoolDish("Тирамису", "Tiramisu", "Tiramisu"),
    PoolDish("Рататуй", "Ratatouille", "Ratatouille"),
    PoolDish("Путин (канадское блюдо)", "Poutine", "Poutine"),
    PoolDish("Фалафель", "Falafel", "Falafel"),
    PoolDish("Пад тай", "Pad thai", "Pad Thai"),
    PoolDish("Шакшука", "Shakshouka", "Shakshuka"),
    PoolDish("Курица гунбао", "Kung Pao chicken", "Kung Pao"),
    PoolDish("Говядина Веллингтон", "Beef Wellington", "Beef Wellington"),
    PoolDish("Фиш-энд-чипс", "Fish and chips", "Fish"),
    PoolDish("Яблочный пирог", "Apple pie", "Apple"),
    PoolDish("Гуляш", "Goulash", "Goulash"),
    PoolDish("Бирьяни", "Biryani", "Biryani"),
    PoolDish("Тонкацу", "Tonkatsu", "Tonkatsu"),
    PoolDish("Карбонара", "Carbonara", "Carbonara"),
    PoolDish("Пельмени", "Dumpling", "Dumpling"),
    PoolDish("Шоколадный торт", "Chocolate cake", "Chocolate"),
]

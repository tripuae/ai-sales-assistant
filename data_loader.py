"""
Data loader for TripUAE tourism pricing system.
Populates the database with tour and pricing information.
"""

import textwrap
import logging
from database_schema import PriceDatabase, TourPackage, TourVariant, PriceOption, TransferOption

# Set up logging for monitoring data loading progress.
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ------------------------------------------------------------------------------
# COMMON CONSTANTS
# Centralize repeated values (e.g., durations) for consistency.
# ------------------------------------------------------------------------------
DESERT_SAFARI_DURATION = "5.5 часов (15:30-21:00)"
NIGHT_CRUISE_PREMIUM_DURATION = "2 часа 15 минут (20:30-22:45)"
NIGHT_CRUISE_STANDARD_DURATION = "1 час (17:30-18:30)"
NIGHT_CRUISE_VIP_DURATION = "1 час 45 минут (21:00-22:45)"
DUBAI_CITY_TOUR_STANDARD_DURATION = "8.5 часов (12:00-20:30)"
DUBAI_CITY_TOUR_PREMIUM_DURATION = "10 часов (13:00-23:00)"

# ------------------------------------------------------------------------------
# NOTE: For greater flexibility in production, consider moving these tour
# definitions to external JSON or YAML configuration files.
# ------------------------------------------------------------------------------

def create_desert_safari_data():
    """Create data for desert safari tours."""
    logger.info("Creating Desert Safari data.")
    package = TourPackage(
        id="desert_jeep_safari",
        name="Пустынное джип-сафари",
        type="excursion",
        description=textwrap.dedent("""\
            Увлекательное путешествие по высоким пышным барханам песчаных дюн.
            Вас ждут несколько остановок, где с наслаждением можно будет любоваться закатом,
            на фоне которого вы сможете сделать великолепные фотографии и видеосъемку.
        """),
        location="Dubai",
        variants={
            "standard": TourVariant(
                name="Стандарт",
                description="Стандартный пакет пустынного сафари с трансфером и питанием",
                duration=DESERT_SAFARI_DURATION,
                pricing={
                    "dubai": PriceOption(
                        adult_price=40,
                        child_price=35,
                        child_age_min=3,
                        child_age_max=11,
                        infant_price=0,
                        infant_age_max=3,
                        notes="Выезд из эмиратов Дубай, Аджман, Шарджа"
                    ),
                    "abu_dhabi": PriceOption(
                        adult_price=75,
                        child_price=65,
                        child_age_min=3,
                        child_age_max=11,
                        notes="Выезд из эмирата Абу-Даби"
                    ),
                    "fujairah": PriceOption(
                        adult_price=70,
                        child_price=65,
                        child_age_min=3,
                        child_age_max=11,
                        notes="Выезд из эмиратов Фуджейра, Умм-Аль-Кувейн, Рас-Аль-Хайма"
                    ),
                },
                includes_transfer=True,
                includes_meals=True,
                available_days=["daily"],
            ),
            "premium": TourVariant(
                name="Премиум",
                description="Премиум пакет пустынного сафари с трансфером и улучшенным питанием",
                duration=DESERT_SAFARI_DURATION,
                pricing={
                    "dubai": PriceOption(
                        adult_price=55,
                        child_price=50,
                        child_age_min=3,
                        child_age_max=11,
                        infant_price=0,
                        infant_age_max=3,
                        notes="Выезд из эмиратов Дубай, Аджман, Шарджа"
                    ),
                },
                includes_transfer=True,
                includes_meals=True,
                available_days=["daily"],
            ),
            "vip": TourVariant(
                name="VIP",
                description="VIP пакет пустынного сафари с трансфером и премиальным обслуживанием",
                duration=DESERT_SAFARI_DURATION,
                pricing={
                    "dubai": PriceOption(
                        adult_price=80,
                        child_price=75,
                        child_age_min=3,
                        child_age_max=11,
                        infant_price=0,
                        infant_age_max=3,
                        notes="Выезд из эмиратов Дубай, Аджман, Шарджа"
                    ),
                },
                includes_transfer=True,
                includes_meals=True,
                available_days=["daily"],
            ),
            "private_standard": TourVariant(
                name="Частное стандартное сафари",
                description="Индивидуальное стандартное пустынное сафари с трансфером",
                duration=DESERT_SAFARI_DURATION,
                pricing={
                    "dubai": PriceOption(
                        adult_price=240,
                        notes="От 1 до 6 человек, выезд из эмиратов Шарджа, Дубай, Аджман"
                    ),
                },
                includes_transfer=True,
                includes_meals=True,
                available_days=["daily"],
                min_participants=1,
            ),
            "private_premium": TourVariant(
                name="Частное премиум сафари",
                description="Индивидуальное премиум пустынное сафари с трансфером",
                duration=DESERT_SAFARI_DURATION,
                pricing={
                    "dubai": PriceOption(
                        adult_price=300,
                        notes="От 1 до 6 человек, выезд из эмиратов Шарджа, Дубай, Аджман"
                    ),
                },
                includes_transfer=True,
                includes_meals=True,
                available_days=["daily"],
                min_participants=1,
            ),
            "private_vip": TourVariant(
                name="Частное VIP сафари",
                description="Индивидуальное VIP пустынное сафари с трансфером",
                duration=DESERT_SAFARI_DURATION,
                pricing={
                    "dubai": PriceOption(
                        adult_price=350,
                        notes="От 1 до 6 человек, выезд из эмиратов Шарджа, Дубай, Аджман"
                    ),
                    "fujairah": PriceOption(
                        adult_price=350,
                        notes="От 1 до 6 человек, выезд из эмиратов Абу-Даби, Фуджейра, Умм-Аль-Кувейн, Рас-Аль-Хайма"
                    ),
                },
                includes_transfer=True,
                includes_meals=True,
                available_days=["daily"],
                min_participants=1,
            ),
        },
        upsell_suggestions=[
            "edge_walk", 
            "atlantis_aquaventure", 
            "wild_wadi"
        ],
    )
    logger.info("Desert Safari data created.")
    return package

def create_night_cruise_data():
    """Create data for Dubai Marina night cruise."""
    logger.info("Creating Night Cruise data.")
    package = TourPackage(
        id="night_cruise",
        name="Ночной круиз по Дубай Марине",
        type="cruise",
        description=textwrap.dedent("""\
            Ночная прогулка по каналу. Во время круиза вы полюбуетесь престижным Дубайским
            кварталом с небоскребами, яхт-клубами и променадом в вечерней подсветке. В меню «шведского стола» -
            блюда континентальной и восточной кухни. В программе шоу - эстрадный вокал или танцы тануры.
        """),
        location="Dubai Marina",
        variants={
            "premium": TourVariant(
                name="Премиум",
                description="Круиз на лодке Доу или Катамаране с ужином, длительностью 2 часа 15 минут",
                duration=NIGHT_CRUISE_PREMIUM_DURATION,
                pricing={
                    "dubai": PriceOption(
                        adult_price=50,
                        child_price=45, 
                        child_age_min=2,
                        child_age_max=11,
                        infant_price=0,
                        infant_age_max=2,
                        notes="С трансфером, выезд из Дубаи"
                    ),
                    "dubai_no_transfer": PriceOption(
                        adult_price=45,
                        child_price=35,
                        child_age_min=2,
                        child_age_max=11,
                        infant_price=0,
                        infant_age_max=2,
                        notes="Без трансфера, выезд из любого Эмирата"
                    ),
                },
                includes_transfer=True,
                includes_meals=True,
                available_days=["daily"],
            ),
            "standard": TourVariant(
                name="Стандарт",
                description="Круиз на лодке Доу или Катамаране без ужина, длительностью 1 час",
                duration=NIGHT_CRUISE_STANDARD_DURATION,
                pricing={
                    "dubai_no_transfer": PriceOption(
                        adult_price=25,
                        child_price=25,
                        child_age_min=2,
                        child_age_max=11,
                        infant_price=0,
                        infant_age_max=2,
                        notes="Без трансфера и без питания, выезд из любого Эмирата"
                    ),
                    "dubai_no_transfer_meal": PriceOption(
                        adult_price=30,
                        child_price=30,
                        child_age_min=2,
                        child_age_max=11,
                        infant_price=0,
                        infant_age_max=2,
                        notes="Без трансфера, с питанием, выезд из любого Эмирата"
                    ),
                },
                includes_transfer=False,
                includes_meals=False,
                available_days=["daily"],
            ),
            "vip": TourVariant(
                name="VIP на лодке Александра",
                description="Круиз на лодке Александра с ужином, длительностью 1 час 45 минут",
                duration=NIGHT_CRUISE_VIP_DURATION,
                pricing={
                    "dubai": PriceOption(
                        adult_price=75,
                        child_price=55, 
                        child_age_min=2,
                        child_age_max=11,
                        infant_price=0,
                        infant_age_max=2,
                        notes="С трансфером, нижняя палуба, выезд из Дубаи"
                    ),
                    "dubai_upper": PriceOption(
                        adult_price=80,
                        child_price=60, 
                        child_age_min=2,
                        child_age_max=11,
                        infant_price=0,
                        infant_age_max=2,
                        notes="С трансфером, верхняя палуба, выезд из Дубаи"
                    ),
                    "sharjah": PriceOption(
                        adult_price=85,
                        child_price=65, 
                        child_age_min=2,
                        child_age_max=11,
                        infant_price=0,
                        infant_age_max=2,
                        notes="С трансфером, нижняя палуба, выезд из Шарджи, Аджмана"
                    ),
                    "sharjah_upper": PriceOption(
                        adult_price=90,
                        child_price=70, 
                        child_age_min=2,
                        child_age_max=11,
                        infant_price=0,
                        infant_age_max=2,
                        notes="С трансфером, верхняя палуба, выезд из Шарджи, Аджмана"
                    ),
                    "no_transfer": PriceOption(
                        adult_price=65,
                        child_price=45, 
                        child_age_min=2,
                        child_age_max=11,
                        infant_price=0,
                        infant_age_max=2,
                        notes="Без трансфера, нижняя палуба, выезд из любого Эмирата"
                    ),
                    "no_transfer_upper": PriceOption(
                        adult_price=70,
                        child_price=50, 
                        child_age_min=2,
                        child_age_max=11,
                        infant_price=0,
                        infant_age_max=2,
                        notes="Без трансфера, верхняя палуба, выезд из любого Эмирата"
                    ),
                },
                includes_transfer=True,
                includes_meals=True,
                available_days=["daily"],
            ),
        },
        upsell_suggestions=[
            "palm_view", 
            "burj_khalifa",
        ],
    )
    logger.info("Night Cruise data created.")
    return package

def create_dubai_city_tour_data():
    """Create data for Dubai City Tour."""
    logger.info("Creating Dubai City Tour data.")
    package = TourPackage(
        id="dubai_city_tour",
        name="Дубай Сити Тур",
        type="excursion",
        description=textwrap.dedent("""\
            Обзорная экскурсия по Дубаю, включающая посещение главных достопримечательностей города.
            Вы увидите знаменитый Бурдж-Халифа, Дубай Молл, Пальмовый остров, Бурдж-Аль-Араб и другие ключевые места города.
        """),
        location="Dubai",
        variants={
            "standard": TourVariant(
                name="Стандарт",
                description="Дубай Сити Тур без прогулки на лодке и питания",
                duration=DUBAI_CITY_TOUR_STANDARD_DURATION,
                pricing={
                    "dubai": PriceOption(
                        adult_price=40,
                        child_price=35,
                        child_age_min=4,
                        child_age_max=11,
                        infant_price=0,
                        infant_age_max=3,
                        notes="С трансфером, выезд из Дубай, Шарджа, Аджман"
                    ),
                    "ras_al_khaimah": PriceOption(
                        adult_price=60,
                        child_price=60,
                        child_age_min=3,
                        child_age_max=11,
                        infant_price=0,
                        infant_age_max=3,
                        notes="С трансфером, выезд из Рас-Аль-Хайма"
                    ),
                    "abu_dhabi": PriceOption(
                        adult_price=60,
                        child_price=60,
                        child_age_min=3,
                        child_age_max=11,
                        infant_price=0,
                        infant_age_max=3,
                        notes="С трансфером, выезд из Абу-Даби"
                    ),
                    "fujairah": PriceOption(
                        adult_price=60,
                        child_price=60,
                        child_age_min=3,
                        child_age_max=11,
                        infant_price=0,
                        infant_age_max=3,
                        notes="С трансфером, выезд из Фуджейра"
                    ),
                },
                includes_transfer=True,
                includes_meals=False,
                available_days=["wednesday", "saturday"],
                notes="Для выездов из Дубай, Шарджа, Аджман доступно в среду и субботу. Для выездов из Абу-Даби, Рас-Аль-Хайма и Фуджейра доступно в понедельник, вторник, четверг, пятницу и воскресенье.",
            ),
            "premium": TourVariant(
                name="Премиум",
                description="Дубай Сити Тур с круизом на лодке и питанием",
                duration=DUBAI_CITY_TOUR_PREMIUM_DURATION,
                pricing={
                    "dubai": PriceOption(
                        adult_price=95,
                        child_price=85,
                        child_age_min=3,
                        child_age_max=11,
                        notes="С трансфером и питанием, выезд из Дубай, Аджман, Шарджа"
                    ),
                    "other_emirates": PriceOption(
                        adult_price=100,
                        child_price=85,
                        child_age_min=3,
                        child_age_max=11,
                        notes="С трансфером и питанием, выезд из Фуджейра, Рас-эль-Хайма, Умм-Аль-Кувейн, Абу-Даби"
                    ),
                    "dubai_burj": PriceOption(
                        adult_price=160,
                        child_price=140,
                        child_age_min=3,
                        child_age_max=11,
                        notes="С трансфером, питанием и билетом на подъем на Бурдж Халифа 124 этаж, выезд из Дубай, Аджман, Шарджа"
                    ),
                    "other_emirates_burj": PriceOption(
                        adult_price=170,
                        child_price=150,
                        child_age_min=3,
                        child_age_max=11,
                        notes="С трансфером, питанием и билетом на подъем на Бурдж Халифа 124 этаж, выезд из Фуджейра, Рас-эль-Хайма, Умм-Аль-Кувейн, Абу-Даби"
                    ),
                },
                includes_transfer=True,
                includes_meals=True,
                available_days=["monday", "tuesday", "thursday", "friday", "sunday"],
            ),
        },
        upsell_suggestions=[
            "burj_khalifa",
            "dubai_aquarium",
        ],
    )
    logger.info("Dubai City Tour data created.")
    return package

def create_transfer_data():
    """Create transfer pricing data."""
    logger.info("Creating Transfer data.")
    transfers = [
        TransferOption(
            from_location="Dubai (Sharjah, Ajman)",
            to_location="Dubai",
            passenger_range="1-7",
            duration="Up to 6 hours",
            price_usd=170
        ),
        TransferOption(
            from_location="Dubai (Sharjah, Ajman)",
            to_location="Dubai",
            passenger_range="1-7",
            duration="More than 6 hours",
            price_usd=200
        ),
        TransferOption(
            from_location="Abu Dhabi",
            to_location="Abu Dhabi",
            passenger_range="1-7",
            duration="Up to 6 hours",
            price_usd=160
        ),
        TransferOption(
            from_location="Abu Dhabi",
            to_location="Abu Dhabi",
            passenger_range="1-7",
            duration="More than 6 hours",
            price_usd=200
        ),
        TransferOption(
            from_location="Dubai (Sharjah, Ajman)",
            to_location="Abu Dhabi",
            passenger_range="1-7",
            duration="7-9 hours",
            price_usd=200
        ),
        TransferOption(
            from_location="Dubai (Sharjah, Ajman)",
            to_location="Abu Dhabi",
            passenger_range="8-14",
            duration="7-9 hours",
            price_usd=360
        ),
        TransferOption(
            from_location="Ras Al Khaimah",
            to_location="Dubai",
            passenger_range="1-7",
            duration="6-8 hours",
            price_usd=220
        ),
        TransferOption(
            from_location="Fujairah",
            to_location="Dubai",
            passenger_range="1-7",
            duration="7-9 hours",
            price_usd=270
        ),
    ]
    logger.info("Transfer data created.")
    return transfers

def create_database():
    """Create and populate the price database."""
    logger.info("Creating the Price Database.")
    try:
        desert_safari = create_desert_safari_data()
        night_cruise = create_night_cruise_data()
        dubai_city_tour = create_dubai_city_tour_data()
        transfers = create_transfer_data()

        db = PriceDatabase(
            tours={
                "desert_jeep_safari": desert_safari,
                "night_cruise": night_cruise,
                "dubai_city_tour": dubai_city_tour,
            },
            transfers=transfers
        )
        logger.info("Price Database created successfully.")
        return db
    except Exception as e:
        logger.error("Error creating database: %s", e)
        raise

if __name__ == "__main__":
    db = create_database()
    print(db.json(indent=2))
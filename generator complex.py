import os
import random
from pathlib import Path
from typing import List, Dict, Tuple
import time
from dotenv import load_dotenv
from enum import Enum
import grpc
from stability_sdk import client
import stability_sdk.interfaces.gooseai.generation.generation_pb2 as generation
import argparse
from collections import defaultdict
import logging
from datetime import datetime

# Emoji constants for logging
EMOJIS = {
    'start': '🚀',
    'color': '🎨',
    'aspect': '📐',
    'generate': '⚙️',
    'success': '✅',
    'error': '❌',
    'warning': '⚠️',
    'info': 'ℹ️',
    'save': '💾',
    'time': '⏱️',
    'config': '⚙️',
    'api': '🔑',
    'batch': '📦',
    'dim': '📏',
    'prompt': '💭',
    'ceramic': '🏺',
    'alien': '👽'
}


class AspectRatio(Enum):
    LANDSCAPE_4_3 = ("4:3", 768, 576)
    PORTRAIT_3_4 = ("3:4", 576, 768)
    LANDSCAPE_16_9 = ("16:9", 832, 468)
    PORTRAIT_9_16 = ("9:16", 468, 832)
    SQUARE_1_1 = ("1:1", 640, 640)

    def __init__(self, ratio_name: str, width: int, height: int):
        self._ratio_name = ratio_name
        self._width = width
        self._height = height

    @property
    def ratio_name(self) -> str:
        return self._ratio_name

    @property
    def width(self) -> int:
        return self._width

    @property
    def height(self) -> int:
        return self._height


class CeramicType(Enum):
    QUANTUM = "quantum"
    DIMENSIONAL = "dimensional"
    STELLAR = "stellar"
    PLANETARY = "planetary"
    BIOLOGIC = "biologic"
    ENERGY = "energy"
    TEMPORAL = "temporal"


class ColorPalette:
    COLOR_FAMILIES = {
        "quantum": {
            "primary": [
                "quantum blue", "probability white", "wave cyan",
                "uncertainty violet", "superposition grey"
            ],
            "energy": [
                "observation gold", "measurement silver", "collapse white",
                "coherence blue", "entanglement purple"
            ],
            "phase": [
                "phase-shift indigo", "quantum-state azure", "wavefunction teal",
                "probability pearl", "quantum-foam white"
            ]
        },
        "dimensional": {
            "spatial": [
                "tesseract blue", "hypercube violet", "dimensional white",
                "void black", "geometry green"
            ],
            "structural": [
                "möbius silver", "klein bottle azure", "topology gold",
                "manifold platinum", "dimension grey"
            ],
            "boundary": [
                "boundary black", "intersection white", "fold blue",
                "curvature silver", "geodesic gold"
            ]
        },
        "stellar": {
            "core": [
                "nebula purple", "stellar blue", "cosmic magenta",
                "nova white", "quasar gold"
            ],
            "energy": [
                "plasma blue", "fusion white", "solar gold",
                "stellar-wind cyan", "radiation yellow"
            ],
            "field": [
                "magnetic purple", "corona gold", "prominence red",
                "stellar-atmosphere blue", "photosphere white"
            ]
        },
        "planetary": {
            "surface": [
                "terrestrial blue", "atmospheric cyan", "mineral green",
                "core orange", "magnetic purple"
            ],
            "atmosphere": [
                "ionosphere blue", "stratosphere cyan", "aurora green",
                "ozone turquoise", "atmospheric pearl"
            ],
            "geological": [
                "mineral gold", "crystal blue", "ore silver",
                "magma orange", "tectonic grey"
            ]
        },
        "biologic": {
            "organic": [
                "bioluminescent cyan", "organic green", "cellular blue",
                "neural white", "membrane pearl"
            ],
            "hybrid": [
                "synthetic purple", "bionic green", "circuit gold",
                "cybernetic silver", "neural-link blue"
            ],
            "structural": [
                "organelle blue", "nucleus purple", "cytoplasm cyan",
                "membrane white", "genetic gold"
            ]
        },
        "energy": {
            "core": [
                "vacuum white", "energy blue", "quantum gold",
                "void purple", "potential cyan"
            ],
            "field": [
                "dark matter black", "void blue", "cosmic purple",
                "entropy grey", "singularity white"
            ],
            "flow": [
                "flux blue", "stream cyan", "current white",
                "flow silver", "dynamic gold"
            ]
        },
        "temporal": {
            "flow": [
                "chronon blue", "temporal white", "timeline silver",
                "paradox purple", "causality gold"
            ],
            "state": [
                "past-echo grey", "future-trace cyan", "present-moment white",
                "time-stream blue", "temporal-void black"
            ],
            "distortion": [
                "time-warp purple", "dilation blue", "entropy white",
                "temporal-shift gold", "chronology grey"
            ]
        }
    }

    @classmethod
    def get_random_type(cls) -> CeramicType:
        return random.choice(list(CeramicType))

    @classmethod
    def get_harmonic_colors(cls, ceramic_type: CeramicType, num_colors: int = None) -> List[str]:
        if num_colors is None:
            num_colors = random.randint(1, 4)

        # Check if ceramic type exists in our color families
        if ceramic_type.value not in cls.COLOR_FAMILIES:
            print(
                f"{EMOJIS['warning']} No specific colors found for {ceramic_type.value}, using quantum type instead")
            type_colors = cls.COLOR_FAMILIES["quantum"]
        else:
            type_colors = cls.COLOR_FAMILIES[ceramic_type.value]

        if num_colors == 1:
            primary_category = next(iter(type_colors.values()))
            return [random.choice(primary_category)]

        elif num_colors == 2:
            categories = random.sample(list(type_colors.keys()), 2)
            return [
                random.choice(type_colors[categories[0]]),
                random.choice(type_colors[categories[1]])
            ]

        elif num_colors == 3:
            categories = random.sample(list(type_colors.keys()), 3)
            return [
                random.choice(type_colors[cat]) for cat in categories
            ]

        else:  # num_colors == 4
            all_colors = []
            categories = list(type_colors.keys())

            while len(all_colors) < 4:
                category = random.choice(categories)
                color = random.choice(type_colors[category])
                if color not in all_colors:
                    all_colors.append(color)

            return all_colors

    @classmethod
    def get_color_weights(cls, num_colors: int) -> List[float]:
        if num_colors == 1:
            return [1.0]
        elif num_colors == 2:
            return [0.6, 0.4]
        elif num_colors == 3:
            return [0.5, 0.3, 0.2]
        else:  # num_colors == 4
            return [0.4, 0.3, 0.2, 0.1]


def get_random_colors() -> Tuple[List[str], List[float], CeramicType]:
    ceramic_type = ColorPalette.get_random_type()
    num_colors = random.randint(1, 4)
    colors = ColorPalette.get_harmonic_colors(ceramic_type, num_colors)
    weights = ColorPalette.get_color_weights(num_colors)
    return colors, weights, ceramic_type


class AlienCeramicsGenerator:
    def __init__(self, colors: List[str]):
        self.setup_logging()
        self.logger.info(
            f"{EMOJIS['start']} Initializing Alien Ceramics Generator")

        load_dotenv()

        # Get API key from environment
        self.api_key = os.getenv('STABILITY_API_KEY')
        if not self.api_key:
            self.logger.error(f"{EMOJIS['error']} No API key found")
            raise ValueError("No API key found. Please set STABILITY_API_KEY")

        try:
            self.stability_api = client.StabilityInference(
                key=self.api_key,
                verbose=True,
                engine="stable-diffusion-xl-1024-v1-0",
            )
            self.logger.info(f"{EMOJIS['api']} API connection established")
        except Exception as e:
            self.logger.error(
                f"{EMOJIS['error']} API connection failed: {str(e)}")
            raise ConnectionError(f"Failed to initialize API client: {str(e)}")

        self.color_manager = ColorPalette() if not colors else None
        self.colors = colors

        self.base_descriptions = [
            "Ethereal alien ceramic vessel",
            "Extraterrestrial pottery artifact",
            "Otherworldly ceramic sculpture",
            "Cosmic clay formation",
            "Interstellar ceramic art piece"
        ]

        self.materials = [
            "with crystalline glaze",
            "with bioluminescent material",
            "with translucent alien clay",
            "of zero-gravity fired porcelain",
            "of living ceramic matter"
        ]

        self.styles = [
            "featuring non-Euclidean geometry",
            "with floating segments held by invisible forces",
            "showing organic forms that defy gravity",
            "with impossibly thin walls and inner glow",
            "displaying seamless transitions between solid and transparent"
        ]

        self.lighting = [
            "illuminated from within",
            "with multiple ethereal light sources",
            "glowing with an otherworldly aura"
            "museum-grade focused lighting",
            "professional exhibition lighting setup",
            "gallery spot lighting with soft fill",
            "archival photography lighting",
            "professional museum documentation lighting"
        ]

        self.camera_settings = [
            "shot with medium format camera",
            "photographed with technical camera",
            "captured with museum documentation equipment",
            "professional archival photography",
            "exhibition catalogue photography"
        ]

        self.composition_settings = [
            "centered composition with proper margins",
            "professionally composed with full artifact visibility",
            "complete view with museum-standard framing",
            "exhibition documentation style",
            "archival composition with neutral space"
        ]

        self.ceramic_classifications = {
            "Quantum Vessels": [
                "probability-shifting vessel with superposition states",
                "quantum-entangled ceramic pair showing synchronized patterns",
                "wave-function ceramic container with observer-dependent form",
                "quantum tunneling vessel with phase-shifting walls",
                "quantum foam inspired ceramic with microscopic wormholes"
            ],

            "Dimensional Artifacts": [
                "hypercube-inspired vessel crossing four-dimensional space",
                "möbius strip ceramic defying conventional geometry",
                "klein bottle ceramic existing in non-euclidean space",
                "tesseract-based vessel with impossible geometry",
                "dimensional-folding container with space-bending properties"
            ],

            "Cosmic Scale": {
                "Stellar": [
                    "nebula-scale installation spanning cosmic proportions",
                    "galaxy-inspired megalithic ceramic structure",
                    "supernova-remnant shaped ceremonial vessel",
                    "pulsar-influenced rotating ceramic monument",
                    "quasar-inspired energy-emitting megalith"
                ],
                "Planetary": [
                    "earth-sized ceremonial vessel",
                    "gas-giant inspired floating ceramic sphere",
                    "asteroid-belt ceramic ring system",
                    "lunar-scale ritual container",
                    "planetary core inspired vessel with magnetic field"
                ],
                "Human": [
                    "personal quantum meditation vessel",
                    "individual consciousness amplification chamber",
                    "single-being probability modifier",
                    "human-scale interdimensional portal frame",
                    "personal zero-point energy collector"
                ]
            },

            "Biological Integration": [
                "self-evolving ceramic with DNA-like structures",
                "biomechanical vessel with organic circuits",
                "neural-network ceramic with synaptic glazing",
                "organic-digital hybrid container",
                "bio-luminescent living ceramic organism"
            ],

            "Temporal Artifacts": [
                "time-dilating ceremonial vessel",
                "entropy-reversing container",
                "chronon-collecting meditation chamber",
                "temporal loop generating sculpture",
                "time-crystal based ceremonial object"
            ],

            "Energy Manifestations": [
                "zero-point energy harvesting vessel",
                "dark energy condensing container",
                "antimatter containment ceremonial object",
                "vacuum energy fluctuation visualizer",
                "quantum field harmonizing sculpture"
            ],

            "Consciousness Interfaces": [
                "telepathic amplification chamber",
                "collective consciousness visualization vessel",
                "psychic energy focusing artifact",
                "mental dimension bridging container",
                "consciousness probability altering device"
            ],

            "Interdimensional Shrines": [
                "multiversal gateway shrine",
                "parallel reality viewing chamber",
                "dimensional intersection oracle",
                "cosmic consciousness temple vessel",
                "universal harmony meditation chamber"
            ]
        }

        self.technological_aspects = [
            "utilizing quantum levitation fields",
            "powered by zero-point energy",
            "incorporating dark matter interfaces",
            "channeling vacuum energy fluctuations",
            "manipulating quantum probability fields",
            "harnessing cosmic background radiation",
            "employing quantum entanglement networks",
            "utilizing temporal field manipulation",
            "incorporating higher dimensional mathematics",
            "featuring quantum coherence maintenance"
        ]

        self.alien_civilizations = [
            "created by Type II civilization utilizing stellar energy",
            "crafted by Type III civilization spanning galaxies",
            "designed by quantum-conscious beings",
            "formed by energy-based lifeforms",
            "manufactured by collective consciousness entities",
            "produced by interdimensional archaeologists",
            "constructed by temporal engineers",
            "designed by cosmic awareness beings",
            "created by universal consciousness architects",
            "crafted by quantum probability shapers"
        ]

        self.scientific_principles = [
            "demonstrating quantum superposition",
            "exhibiting temporal causality loops",
            "manifesting quantum entanglement effects",
            "showing evidence of dimensional folding",
            "displaying quantum tunneling properties",
            "incorporating probability field manipulation",
            "utilizing quantum coherence preservation",
            "demonstrating wave-particle duality",
            "exhibiting quantum field interactions",
            "manifesting space-time curvature"
        ]

        self.cosmic_purposes = [
            "designed for universal energy harmonization",
            "created for quantum probability manipulation",
            "used in cosmic consciousness exploration",
            "purposed for dimensional boundary studies",
            "intended for temporal field research",
            "designed for quantum state observation",
            "created for cosmic energy collection",
            "used in universal consciousness meditation",
            "purposed for quantum reality navigation",
            "intended for multiversal communication"
        ]

        # self.backgrounds = [
        #     "on neutral museum background",
        #     "against professional photography backdrop",
        #     "on gradient museum backdrop",
        #     "with gallery-standard neutral background",
        #     "against conservation-grade backdrop"
        # ]

    def setup_logging(self):
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = log_dir / f"ceramic_generation_{timestamp}.log"

        self.logger = logging.getLogger("AlienCeramics")
        self.logger.setLevel(logging.INFO)

        file_handler = logging.FileHandler(log_file)
        console_handler = logging.StreamHandler()

        file_formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s')
        console_formatter = logging.Formatter('%(message)s')

        file_handler.setFormatter(file_formatter)
        console_handler.setFormatter(console_formatter)

        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)

    def get_random_aspect_ratio(self) -> AspectRatio:
        return random.choice(list(AspectRatio))

    def generate_prompt(self, aspect_ratio: AspectRatio) -> str:
        # chosen_color = self.color_manager.get_next_color()
        # self.logger.info(f"{EMOJIS['color']} Selected color: {chosen_color}")

        # Select random categories
        category = random.choice(list(self.ceramic_classifications.keys()))
        if category == "Cosmic Scale":
            scale = random.choice(
                list(self.ceramic_classifications["Cosmic Scale"].keys()))
            base_desc = random.choice(
                self.ceramic_classifications["Cosmic Scale"][scale])
        else:
            base_desc = random.choice(self.ceramic_classifications[category])

        composition_hints = {
            AspectRatio.LANDSCAPE_4_3: "wide composition, horizontal framing",
            AspectRatio.PORTRAIT_3_4: "vertical composition, tall framing",
            AspectRatio.LANDSCAPE_16_9: "cinematic wide composition",
            AspectRatio.PORTRAIT_9_16: "vertical cinematic composition",
            AspectRatio.SQUARE_1_1: "centered composition"
        }

        # Get color description
        if self.colors:
            color_desc = f"predominantly {random.choice(self.colors)}"
        else:
            colors, weights, _ = get_random_colors()
            color_desc = f"predominantly {colors[0]}"

        components = [
            f"Advanced alien ceramic artifact: {base_desc}",
            color_desc,
            random.choice(self.technological_aspects),
            random.choice(self.alien_civilizations),
            random.choice(self.scientific_principles),
            random.choice(self.cosmic_purposes),
            random.choice(self.lighting),
            random.choice(self.camera_settings),
            random.choice(self.composition_settings),
            # random.choice(self.backgrounds),
            composition_hints[aspect_ratio],
            random.choice(self.base_descriptions),
            random.choice(self.materials),
            random.choice(self.styles),
            "professional museum photography, sharp focus, high detail, proper exposure, full framing, uniform lighting, clear edges, 8k, highly detailed, professional color accuracy"
            # "professional product photography, studio lighting, 8k, highly detailed"
        ]
        # Log the cosmic classification for this generation
        self.logger.info(
            f"{EMOJIS['alien']} Cosmic Classification: {category}")
        if category == "Cosmic Scale":
            self.logger.info(f"{EMOJIS['info']} Scale Category: {scale}")

        # return ", ".join(components), chosen_color
        return ", ".join(components)

    def generate_batch(self,
                       num_images: int,
                       output_dir: str = "alien_ceramics",
                       seed: int = None) -> List[Dict]:
        self.logger.info(
            f"\n{EMOJIS['batch']} Starting batch generation of {num_images} images")

        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        self.logger.info(f"{EMOJIS['info']} Output directory: {output_path}")

        generated_images = []

        for i in range(num_images):
            aspect_ratio = self.get_random_aspect_ratio()
            prompt = self.generate_prompt(aspect_ratio)

            try:
                self.logger.info(
                    f"\n{EMOJIS['generate']} Generating image {i+1}/{num_images}")
                self.logger.info(
                    f"{EMOJIS['aspect']} Aspect Ratio: {aspect_ratio.ratio_name}")
                self.logger.info(
                    f"{EMOJIS['dim']} Dimensions: {aspect_ratio.width}x{aspect_ratio.height}")
                self.logger.info(f"{EMOJIS['prompt']} Prompt: {prompt}")

                generation_start = time.time()

                answers = self.stability_api.generate(
                    prompt=prompt,
                    seed=seed if seed else random.randint(0, 1000000),
                    # steps=40,
                    # cfg_scale=8.0,
                    steps=50,
                    cfg_scale=7.5,
                    width=aspect_ratio.width,
                    height=aspect_ratio.height,
                    samples=1,
                    sampler=generation.SAMPLER_K_DPMPP_2M
                )
                generation_time = time.time() - generation_start

                for j, answer in enumerate(answers):
                    filename = output_path / \
                        f"ceramic_{i}_{aspect_ratio.ratio_name.replace(':', '_')}_{j}.png"
                    with open(filename, 'wb') as f:
                        f.write(answer.artifacts[0].binary)

                    generated_images.append({
                        'filename': str(filename),
                        'prompt': prompt,
                        'aspect_ratio': aspect_ratio.ratio_name,
                        'dimensions': f"{aspect_ratio.width}x{aspect_ratio.height}",
                        'seed': seed if seed else None,
                        'generation_time': f"{generation_time:.2f}s"
                    })

                    self.logger.info(
                        f"{EMOJIS['save']} Saved image to: {filename}")
                    self.logger.info(
                        f"{EMOJIS['time']} Generation time: {generation_time:.2f}s")

                self.logger.info(
                    f"{EMOJIS['success']} Successfully generated image {i+1}")
                time.sleep(0.5)

            except grpc.RpcError as e:
                if e.code() == grpc.StatusCode.UNAUTHENTICATED:
                    self.logger.error(
                        f"{EMOJIS['error']} Authentication failed")
                    break
                elif e.code() == grpc.StatusCode.RESOURCE_EXHAUSTED:
                    self.logger.warning(
                        f"{EMOJIS['warning']} Rate limit reached. Waiting...")
                    time.sleep(5)
                    continue
                else:
                    self.logger.error(
                        f"{EMOJIS['error']} Error generating image {i+1}: {str(e)}")
                    continue
            except Exception as e:
                self.logger.error(
                    f"{EMOJIS['error']} Unexpected error: {str(e)}")
                continue

        return generated_images


def main():
    parser = argparse.ArgumentParser(
        description='Generate alien ceramic images with specified or automatic colors',
        formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument('colors', nargs='*',
                        help='Optional: Colors to be used in the images')
    parser.add_argument('-n', '--num-images', type=int, default=5,
                        help='Number of images to generate')
    parser.add_argument('-o', '--output-dir', default='alien_ceramics_batch',
                        help='Output directory')
    parser.add_argument('--type', choices=[t.value for t in CeramicType],
                        help='Optional: Specify ceramic type for color selection')

    args = parser.parse_args()

    try:
        env_path = Path('.env')
        if not env_path.exists():
            api_key = input(
                f"{EMOJIS['api']} Please enter your Stability AI API key: ")
            with open(env_path, 'w') as f:
                f.write(f"STABILITY_API_KEY={api_key}")
            print(f"{EMOJIS['success']} Created .env file with API key")

        if not args.colors:
            # Use automatic color selection
            if args.type:
                ceramic_type = CeramicType(args.type)
            else:
                ceramic_type = ColorPalette.get_random_type()

            colors, weights, _ = get_random_colors()
            print(f"\n{EMOJIS['info']} Using automatic color selection:")
            print(f"{EMOJIS['ceramic']} Ceramic Type: {ceramic_type.value}")
            print(f"{EMOJIS['color']} Generated color palette:")
            for color, weight in zip(colors, weights):
                print(f"  - {color} (weight: {weight*100:.1f}%)")
        else:
            colors = args.colors

        generator = AlienCeramicsGenerator(colors)

        results = generator.generate_batch(
            num_images=args.num_images,
            output_dir=args.output_dir
        )

        print(f"\n{EMOJIS['info']} Generation Summary:")
        for result in results:
            print(f"\n{EMOJIS['ceramic']} Filename: {result['filename']}")
            print(f"{EMOJIS['aspect']} Aspect Ratio: {result['aspect_ratio']}")
            print(f"{EMOJIS['dim']} Dimensions: {result['dimensions']}")
            print(f"{EMOJIS['prompt']} Prompt: {result['prompt']}")
            print(
                f"{EMOJIS['time']} Generation Time: {result['generation_time']}")
            if result['seed']:
                print(f"{EMOJIS['info']} Seed: {result['seed']}")

    except ValueError as e:
        print(f"{EMOJIS['error']} Configuration error: {str(e)}")
    except ConnectionError as e:
        print(f"{EMOJIS['error']} Connection error: {str(e)}")
    except Exception as e:
        print(f"{EMOJIS['error']} An unexpected error occurred: {str(e)}")


if __name__ == "__main__":
    main()

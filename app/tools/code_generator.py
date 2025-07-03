import ast
from typing import List, Dict, Any, Optional
from langchain.tools import Tool
import re
from loguru import logger
from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate
from app.config import OPENAI_API_KEY

ALLOWED_MANIM_CLASSES = {
    "Scene",
    "Text",
    "Circle",
    "Square",
    "Rectangle",
    "Triangle",
    "Arrow",
    "Line",
    "Dot",
    "VGroup",
    "MathTex",
    "Tex",
    "Write",
    "FadeIn",
    "FadeOut",
    "GrowFromCenter",
    "Transform",
    "Create",
    "Uncreate",
    "DrawBorderThenFill",
}

ALLOWED_MANIM_METHODS = {
    "play",
    "wait",
    "add",
    "remove",
    "clear",
    "get_center",
    "shift",
    "scale",
    "rotate",
    "flip",
    "move_to",
    "next_to",
    "to_edge",
    "to_corner",
    "align_to",
    "arrange",
}


class CodeValidator(ast.NodeVisitor):
    def __init__(self):
        self.errors: List[str] = []
        self.has_scene_class = False
        self.has_construct_method = False

    def visit_Import(self, node):
        for name in node.names:
            if name.name != "manim":
                self.errors.append(
                    f"Only manim imports are allowed, found: {name.name}"
                )
        self.generic_visit(node)

    def visit_ImportFrom(self, node):
        if node.module != "manim":
            self.errors.append(
                f"Only imports from manim are allowed, found: {node.module}"
            )
        # for name in node.names:
        #     if (
        #         name.name not in ALLOWED_MANIM_CLASSES
        #         and name.name not in ALLOWED_MANIM_METHODS
        #     ):
        #         self.errors.append(f"Unauthorized manim import: {name.name}")
        self.generic_visit(node)

    def visit_ClassDef(self, node):
        # Check if it's a Scene subclass
        for base in node.bases:
            if isinstance(base, ast.Name) and base.id == "Scene":
                self.has_scene_class = True
        self.generic_visit(node)

    def visit_FunctionDef(self, node):
        if node.name == "construct":
            self.has_construct_method = True
        self.generic_visit(node)

    def visit_Call(self, node):
        # Check for potentially dangerous function calls
        if isinstance(node.func, ast.Name):
            if node.func.id in ["eval", "exec", "open", "system", "__import__"]:
                self.errors.append(f"Unauthorized function call: {node.func.id}")
        self.generic_visit(node)


def validate_manim_code(code: str) -> List[str]:
    """
    Validate the generated Manim code for safety and correctness.
    Returns a list of errors, empty if code is valid.
    """
    try:
        tree = ast.parse(code)
        validator = CodeValidator()
        validator.visit(tree)

        errors = validator.errors

        if not validator.has_scene_class:
            errors.append("No Scene class found in the code")
        if not validator.has_construct_method:
            errors.append("No construct method found in the Scene class")

        return errors
    except SyntaxError as e:
        return [f"Syntax error in code: {str(e)}"]
    except Exception as e:
        return [f"Error validating code: {str(e)}"]


def extract_scene_class(code: str) -> Optional[str]:
    """
    Extract the scene class name from the code.
    """
    match = re.search(r"class\s+(\w+)\s*\(\s*Scene\s*\)", code)
    return match.group(1) if match else None


def create_code_template(animation_type: str) -> str:
    """
    Create a template for animations that demonstrates best practices and common patterns.
    The template serves as a starting point and can be customized based on specific needs.
    """
    return '''
from manim import *

class AnimationScene(Scene):
    def construct(self):
        # Scene configuration
        # You can customize background color, camera settings, etc.
        # self.camera.background_color = "#333333"
        
        # ===== Object Creation =====
        # Create your visual elements here
        # Examples:
        # - Text elements
        title = Text("Your Title", font_size=48)
        subtitle = Text("Your Subtitle", font_size=32)
        
        # - Geometric shapes
        shapes = VGroup(
            Circle(radius=1.0),
            Square(side_length=2.0),
            Triangle()
        ).arrange(RIGHT, buff=0.5)
        
        # - Mathematical elements
        equation = MathTex(r"E = mc^2")
        
        # ===== Initial Layout =====
        # Position your elements
        title.to_edge(UP)
        subtitle.next_to(title, DOWN)
        shapes.move_to(ORIGIN)
        equation.to_edge(DOWN)
        
        # ===== Animation Sequence =====
        # 1. Introduction sequence
        self.play(Write(title))
        self.wait(0.5)
        self.play(FadeIn(subtitle))
        self.wait()
        
        # 2. Main content
        # Animate shapes one by one
        for shape in shapes:
            self.play(Create(shape))
        self.wait()
        
        # Group animation example
        self.play(
            shapes.animate.scale(0.8),
            equation.animate.scale(1.2)
        )
        self.wait()
        
        # Transform example
        self.play(
            Transform(shapes[0], shapes[1]),
            shapes[2].animate.rotate(PI/2)
        )
        self.wait()
        
        # 3. Cleanup sequence
        # Remove elements gracefully
        self.play(
            FadeOut(title),
            FadeOut(subtitle),
            FadeOut(shapes),
            FadeOut(equation)
        )
        
        # Optional final pause
        self.wait()

    def create_highlighted_text(self, text: str, color: str = YELLOW) -> Text:
        """Helper method for creating consistently styled text with highlights"""
        return Text(text, color=color)
    
    def create_annotation(self, text: str, reference_obj: Mobject) -> Text:
        """Helper method for creating annotations that point to other objects"""
        annotation = Text(text, font_size=24)
        annotation.next_to(reference_obj, RIGHT)
        return annotation
'''


def generate_manim_code(prompt: str) -> str:
    """
    Generate Manim code based on the prompt using LLM.
    """
    try:
        # Initialize the LLM
        llm = ChatOpenAI(
            model="o4-mini",
            api_key=OPENAI_API_KEY,
        )

        # Create the prompt template
        template = """You are a world-class Python developer and animation expert, specializing in creating stunning visualizations using the Manim mathematical animation library. Your deep understanding of both programming principles and animation aesthetics allows you to create elegant, efficient, and visually appealing animations.

        Your task is to generate clean, well-structured Python code for a Manim animation based on the following description.

        Core Principles to Follow:
        1. Code Structure and Style:
           - Write clean, modular, and well-commented code
           - Follow PEP 8 style guidelines
           - Use meaningful variable names that reflect their purpose
           - Break complex animations into logical steps
           - Add comments explaining the purpose of each major section

        2. Animation Best Practices:
           - Ensure smooth transitions between animation states
           - Use appropriate timing for visual clarity (self.wait())
           - Group related animations when appropriate
           - Consider the visual hierarchy and composition
           - Implement proper object cleanup after use

        3. Technical Requirements:
           - Only use these allowed Manim classes: {allowed_classes}
           - Only use these allowed Manim methods: {allowed_methods}
           - Always use 'from manim import *' for imports
           - Every animation must be in a Scene class
           - Implement the construct method
           - Ensure all objects are properly removed from scene (e.g., FadeOut)
           - Focus on safe operations (no file/system operations)

        4. Animation Flow Guidelines:
           - Start with object creation and initial setup
           - Build complexity gradually
           - Use appropriate pacing (wait calls between significant changes)
           - End scenes cleanly with proper object cleanup
           - Consider the viewer's perspective and attention

        5. Spatial Management and Canvas Awareness:
           - Prevent objects from overlapping unintentionally
           - Keep all elements within the visible canvas boundaries
           - Use proper spacing between elements (buff parameter)
           - Utilize layout methods (arrange, next_to, shift) for precise positioning
           - Consider the aspect ratio and scale of all objects
           - Plan the spatial journey of animated elements to avoid collisions
           - Use coordinate system wisely (UP, DOWN, LEFT, RIGHT, ORIGIN)
           - Group related objects using VGroup for better spatial management
           - Test object positions before animations to ensure visibility
           - Consider final positions of transformed objects

        Description of the desired animation:
        {prompt}

        Generate ONLY the Python code without any explanation or markdown formatting. The code should be complete, well-commented, and ready to run.
        """

        prompt_template = PromptTemplate(
            input_variables=["allowed_classes", "allowed_methods", "prompt"],
            template=template,
        )

        # Format the prompt
        formatted_prompt = prompt_template.format(
            allowed_classes=", ".join(ALLOWED_MANIM_CLASSES),
            allowed_methods=", ".join(ALLOWED_MANIM_METHODS),
            prompt=prompt,
        )

        # Generate code using LLM
        code = llm.invoke(formatted_prompt).content

        # Validate the generated code
        errors = validate_manim_code(code)
        if errors:
            logger.error(f"Generated code validation failed: {errors}")
            raise ValueError(f"Generated code is invalid: {', '.join(errors)}")

        return code

    except Exception as e:
        logger.error(f"Failed to generate code: {str(e)}")
        raise


def get_code_generation_tool() -> Tool:
    """
    Create a LangChain tool for generating Manim code.
    """
    return Tool(
        name="generate_manim_code",
        func=generate_manim_code,
        description="""Generate Manim code for creating animations.
        Input should be a detailed description of the desired animation.
        The description should include:
        - What elements to include (text, shapes, equations)
        - How they should move or transform
        - Timing preferences (if any)
        - Color and style preferences (if any)
        - Any specific effects or transitions
        
        Example input: "Create a text animation that shows 'Hello World' appearing letter by letter in blue color, then scaling up and fading out"
        
        Returns the generated Python code as a string.""",
    )

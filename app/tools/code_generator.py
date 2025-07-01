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
    Create a template for different types of animations.
    """
    templates = {
        "text": """
    from manim import *

    class TextScene(Scene):
        def construct(self):
            # Create and display text
            text = Text("{text}")
            self.play(Write(text))
            self.wait()
            # Add some animation
            self.play(text.animate.scale(1.5))
            self.wait()
            self.play(FadeOut(text))
    """,
        "shape": """
    from manim import *

    class ShapeScene(Scene):
        def construct(self):
            # Create shapes
            circle = Circle()
            square = Square()
            
            # Position them
            square.next_to(circle, RIGHT)
            
            # Animate them
            self.play(Create(circle), Create(square))
            self.wait()
            self.play(
                circle.animate.scale(1.5),
                square.animate.rotate(PI/2)
            )
            self.wait()
            self.play(FadeOut(circle), FadeOut(square))
        """,
        "math": """
    from manim import *

    class MathScene(Scene):
        def construct(self):
            # Create mathematical equation
            equation = MathTex("{equation}")
            
            # Animate it
            self.play(Write(equation))
            self.wait()
            self.play(equation.animate.scale(1.5))
            self.wait()
            self.play(FadeOut(equation))
    """,
    }
    return templates.get(animation_type, templates["text"])


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
        template = """You are an expert in creating animations using the Manim library. Your task is to generate Python code for a Manim animation based on the following description.

        Rules and Requirements:
        1. Only use allowed Manim classes: {allowed_classes}
        2. Only use allowed Manim methods: {allowed_methods}
        3. Code must follow this structure:
        - Import from manim
        - Define a Scene class
        - Implement the construct method
        4. Include appropriate timing and wait calls
        5. Add helpful comments explaining the animation steps
        6. Ensure all objects are properly cleaned up (e.g., FadeOut)
        7. Use only safe operations (no file/system operations)

        Description of the desired animation:
        {prompt}

        Generate ONLY the Python code without any explanation or markdown formatting. The code should be complete and ready to run.
        always use from manim import * , don't use any other imports individually.
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

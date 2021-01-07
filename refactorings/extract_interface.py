from antlr4 import *
from antlr4.TokenStreamRewriter import TokenStreamRewriter

from gen.javaLabeled.JavaParserLabeled import JavaParserLabeled
from gen.javaLabeled.JavaParserLabeledListener import JavaParserLabeledListener


class ExtractInterfaceListener(JavaParserLabeledListener):
    def __init__(self, class_name: str = None, interface_name: str = None, common_token_stream=None,
                 public_or_private: str = None):
        self.class_name = class_name
        self.interface_name = interface_name
        if common_token_stream is not None:
            self.token_stream_rewriter = TokenStreamRewriter(common_token_stream)
        else:
            raise TypeError('common_token_stream is None')
        self.public_or_private = public_or_private
        self.is_enter_class = False
        self.interface_code = ''
        self.method_params = {}

    def enterClassDeclaration(self, ctx: JavaParserLabeled.ClassDeclarationContext):
        if ctx.IDENTIFIER().getText() == self.class_name:
            self.is_enter_class = True
            self.interface_code += f'{self.public_or_private} interface {self.interface_name} {"{"}\n'

    def enterMethodDeclaration(self, ctx: JavaParserLabeled.MethodDeclarationContext):
        if self.is_enter_class:
            method_name = ctx.IDENTIFIER().getText()
            self.method_params[method_name] = []

    def enterFormalParameter(self, ctx: JavaParserLabeled.FormalParameterContext):
        grand_parent = ctx.parentCtx.parentCtx.parentCtx
        method_name = grand_parent.IDENTIFIER().getText()
        self.method_params[method_name].append(f'{ctx.typeType().getText()} {ctx.variableDeclaratorId().getText()}')

    def exitMethodDeclaration(self, ctx: JavaParserLabeled.MethodDeclarationContext):
        method_name = ctx.IDENTIFIER().getText()
        method_type = ctx.typeTypeOrVoid().getText()
        if self.is_enter_class:
            if method_name in self.method_params.keys():
                self.interface_code += f'\t{method_type} {method_name}({", ".join(self.method_params[method_name])});\n'
            else:
                self.interface_code += f'\t{method_type} {method_name}();\n'

    def exitClassDeclaration(self, ctx: JavaParserLabeled.ClassDeclarationContext):
        if ctx.IDENTIFIER().getText() == self.class_name:
            self.is_enter_class = False
            self.interface_code += '}\n'
            self.token_stream_rewriter.insertBefore(program_name=self.token_stream_rewriter.DEFAULT_PROGRAM_NAME,
                                                    index=ctx.start.tokenIndex, text=self.interface_code)
            self.token_stream_rewriter.replace(program_name=self.token_stream_rewriter.DEFAULT_PROGRAM_NAME,
                                               from_idx=ctx.start.tokenIndex,
                                               to_idx=ctx.start.tokenIndex + 1 + len(self.class_name),
                                               text=f'class {self.class_name} implements {self.interface_name}')

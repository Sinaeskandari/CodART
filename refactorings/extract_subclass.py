from antlr4 import *
from antlr4.TokenStreamRewriter import TokenStreamRewriter

from gen.javaLabeled.JavaParserLabeled import JavaParserLabeled
from gen.javaLabeled.JavaParserLabeledListener import JavaParserLabeledListener


class ExtractSubclassListener(JavaParserLabeledListener):
    def __init__(self, class_name: str = None, subclass_name: str = None, methods=[], common_token_stream=None):
        self.class_name = class_name
        self.subclass_name = subclass_name
        self.methods = []
        if common_token_stream is not None:
            self.token_stream_rewriter = TokenStreamRewriter(common_token_stream)
        else:
            raise TypeError('common_token_stream is None')
        self.is_enter_class = False
        self.code = ''
        self.method_params = {}
        for m in methods:
            self.method_params[m] = []

    def enterClassDeclaration(self, ctx: JavaParserLabeled.ClassDeclarationContext):
        if ctx.IDENTIFIER().getText() == self.class_name:
            self.is_enter_class = True

    def enterFormalParameter(self, ctx: JavaParserLabeled.FormalParameterContext):
        grand_parent = ctx.parentCtx.parentCtx.parentCtx
        method_name = grand_parent.IDENTIFIER().getText()
        if method_name in self.methods:
            self.method_params[method_name].append(f'{ctx.typeType().getText()} {ctx.variableDeclaratorId().getText()}')

    def exitMethodDeclaration(self, ctx: JavaParserLabeled.MethodDeclarationContext):
        method_name = ctx.IDENTIFIER().getText()
        if self.is_enter_class and method_name in self.method_params.keys():
            method_body = ctx.methodBody().getText().replace('{', '{\n\t\t').replace(';', ';\n\t\t').replace('\t}', '}\n')
            method_type = ctx.typeTypeOrVoid().getText()
            method_params = self.method_params[method_name]
            params = ', '.join(method_params)
            self.methods.append(f'\t{method_type} {method_name}({params}){method_body}')
            self.token_stream_rewriter.delete(self.token_stream_rewriter.DEFAULT_PROGRAM_NAME, ctx.start, ctx.stop)

    def exitClassDeclaration(self, ctx: JavaParserLabeled.ClassDeclarationContext):
        if ctx.IDENTIFIER().getText() == self.class_name:
            self.is_enter_class = False
            self.code += f'\nclass {self.subclass_name} extends {self.class_name} {"{"}'
            for method in self.methods:
                self.code += '\n' + method
            self.code += '}\n'
            self.token_stream_rewriter.insertAfter(index=ctx.stop.tokenIndex,
                                                   program_name=self.token_stream_rewriter.DEFAULT_PROGRAM_NAME,
                                                   text=self.code)

using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text;
using System.Threading.Tasks;
using Sedna.Core.Internals;
using Sedna.Core.Internals.Ast;
using System.Collections;

namespace Sedna.Core
{
    public class Compiler
    {
        private static CompilerScope _Scope  = new CompilerScope();

        public Compiler()
        {
            
        }

        public void DumpTokenTree(List<Token> body, int indent) {
            String pad = new string(' ', indent);
            foreach (Token token in body) {
                Console.WriteLine(
                    string.Format("{0} type: {4} hdr: {1} raw: {2} pos: {3}", 
                        pad, token.RawHeader, 
                        token.Raw, token.Position,
                        token.GetType().Name
                    )
                );

                if (token.Body.Count > 0) {
                    DumpTokenTree(token.Body, indent + 1);
                }
            }
        }

        public void DumpParsed(List<IAst> root, int indent) {
            String pad = new string(' ', indent);

            if (root == null) {
                return;
            }

            foreach (IAst node in root) {
                if (node == null) {
                    continue;
                }

                Token node_token = node.Raw;

                Console.WriteLine(string.Format(
                    "{1} @dump-ast-node type: {0}",
                    node.GetType().Name, pad
                ));

                if (node is ScopeStmt) {

                } else if (node is ImportStmt) {
                    ImportStmt imp_stmt = node as ImportStmt;
                    Console.WriteLine(string.Format(" import-scope: {0}", imp_stmt.ScopeName));
                } else if (node is TypeStmt) {
                    TypeStmt type_stmt = node as TypeStmt;

                    Console.WriteLine(string.Format(
                        "{2} type; Name: {0} BaseType: {1}", type_stmt.Name, type_stmt.BaseType, pad
                    ));

                    foreach (string attr in type_stmt.Attributes) {
                        Console.WriteLine(string.Format(
                            "{2} attribute: {0}", attr, pad
                        ));
                    }

                    DumpParsed(type_stmt.Body, indent + 1);
                } else if (node is FnStmt) {
                    FnStmt fn_stmt = node as FnStmt;
                    Console.WriteLine(string.Format(
                        "{2} name: {0} ret-type: {1}", fn_stmt.Name, fn_stmt.ReturnType, pad
                    ));

                    foreach (string attr in fn_stmt.Attributes) {
                        Console.WriteLine(string.Format(
                            "{0} attribute: {1}", pad, attr
                        ));
                    }

                    DumpParsed(fn_stmt.Body, indent + 1);
                } else if (node is DecStmt) {
                    DecStmt dec_stmt = node as DecStmt;
                    Console.WriteLine(string.Format(
                        "{0} name: {1} type: {2}",
                        pad, dec_stmt.Name, dec_stmt.Type
                    ));

                    List<IAst> tmp = new List<IAst>();

                    tmp.Add(dec_stmt.Value);

                    DumpParsed(tmp, indent + 1);
                } else if (node is InvokeStmt) {
                    InvokeStmt inv_stmt = node as InvokeStmt;

                    Console.WriteLine(string.Format(
                        "{0} path: {1}", pad, inv_stmt.Path
                    ));

                    DumpParsed(inv_stmt.Params, indent + 1);
                } else if (node is ValueStmt) {
                    ValueStmt val_stmt = node as ValueStmt;

                    Console.WriteLine(string.Format(
                        "{0} value: {1}", pad, val_stmt.Value
                    ));

                    DumpParsed(val_stmt.Body, indent + 1);
                } else if (node is Expression) {
                    Expression exp = node as Expression;
                    Console.WriteLine(string.Format(
                        "{0} expression", pad
                    ));

                    DumpParsed(exp.Body, indent + 1);
                } else if (node is ExpressionPart) {
                    ExpressionPart part = node as ExpressionPart;

                    Console.WriteLine(string.Format(
                        "{0} exp-part: {1}", pad, part.ToString()
                    ));
                }
            }
        }

        public void Compile(List<string> src, string Output, string target)
        {
            /*
                Steps:
                1. Tokenize
                2. Parse
                3. Astyfie
                4. Assemble
            */
            _Scope = new CompilerScope();
           
            var bc = new ByteCode();

            foreach (var i in src)
            {
                var x = Parser.Parse(File.ReadAllText(i));

                Console.WriteLine("@dump");
                DumpParsed(x, 1);

                if (!CheckErrors()) return;
                bc.Emit(x);
            }

            bc.Write(Output);
           
        }

        public static  bool CheckErrors()
        {
            if (Parser.Errors.Count == 0 && _Scope.Errors.Count == 0)
            {
                return true;
            }
            else
            {
                Console.WriteLine("Found Errors:");
                foreach (var i in Parser.Errors)
                {
                    Console.WriteLine(i);
                }

                foreach (var i in _Scope.Errors)
                {
                    Console.WriteLine(i);
                }
                return false;
            }
        }  
    }
}

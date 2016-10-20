using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

namespace Sedna.Core.Internals.Ast
{
	public class Expression : IAst {
		public List<IAst> Body { get; set; } = new List<IAst>();

		// This is not supported.
		public override IAst Parse(Token token) {
			// TODO: Throw exception maybe?
			return null;
		}

		// This is not really supported.
		public override bool IsValid(Token token) => false;
	}

	public class ExpressionPart : IAst {
		// The first phase creates these types.
		public string StringValue { get; set; } = "";
		// All numbers are positive at this stage. The negative
		// sign is encoded as a subtraction.
		public char NumberBits { get; set; } = (char)0;
		public uint[] Number { get; set; } = null;
		public bool IsVarRef { get; set; } = false;
		public bool IsString { get; set; } = false;
		public bool IsNumber { get; set; } = false;
		public bool IsParathesis { get; set; } = false;
		public bool IsParaOpen { get; set; } = false;
		public bool IsParaClose { get; set; } = false;
		public bool IsShiftRight { get; set; } = false;
		public bool IsShiftLeft { get; set; } = false;
		public bool IsBitOr { get; set; } = false;
		public bool IsBitAnd { get; set; } = false;
		public bool IsBitXor { get; set; } = false;
		public bool IsLogOr { get; set; } = false;
		public bool IsLogAnd { get; set; } = false;
		public bool IsLogXor { get; set; } = false;
		public bool IsModulus { get; set; } = false;
		public bool IsSquare { get; set; } = false;
		public bool IsSquareOpen { get; set; } = false;
		public bool IsSquareClose { get; set; } = false;
		public bool IsAdd { get; set; } = false;
		public bool IsSub { get; set; } = false;
		public bool IsMul { get; set; } = false;
		public bool IsDiv { get; set; } = false;
		public bool IsComma { get; set; } = false;
		public bool IsCmpEq { get; set; } = false;
		public bool IsCmpEqGr { get; set; } = false;
		public bool IsCmpEqLs { get; set; } = false;
		public bool IsCmpGr { get; set; } = false;
		public bool IsCmpLs { get; set; } = false;
		public bool IsCmpNotEq { get; set; } = false;
		public bool IsAssign { get; set; } = false;

		public override string ToString() {
			return StringValue;
		}

		// The second phase creates these types. I may make
		// these types part of the abstract syntax tree, but
		// have them now to remind me about them. Obviously,
		// some of the others will also likely become part of
		// the AST such as operations, shifts, comparisons, and
		// such forth.
		public bool IsCast { get; set; } = false;
		public bool IsNew { get; set; } = false;
		public bool IsIndex { get; set; } = false;

		// This is not supported.
		public override IAst Parse(Token token) {
			// TODO: Throw exception maybe?
			return null;
		}

		// This is not really supported.
		public override bool IsValid(Token token) => false;
	}

    public class ValueStmt : IAst
    {
        public string Value { get; set; } = "";

        public List<IAst> Body { get; set; } = null;

        public bool IsString { get; set; } = false;
        public bool IsNumber { get; set; } = false;
        public bool IsExpression { get; set; } = false;

        public override bool IsValid(Token raw) => true;

        public override IAst Parse(Token token) {
        	string 					raw;
         	bool 					inside_string;
         	bool					inside_number;
         	bool 					inside_var_ref;
         	int 					tmp;
         	List<IAst>  			linear;
         	StringBuilder   		numdigits;
         	StringBuilder			var_ref;

         	numdigits = new StringBuilder();
         	var_ref = new StringBuilder();
         	linear = new List<IAst>();

         	var_ref.Append(token.Raw);
         	// The special end character. I am hoping this
         	// is characters and not bytes so that it will
         	// be compatible for unicode. This helps make 
         	// the loop below easy to implement and less
         	// code by being able to place all logic inside
         	// the loop and not have to do any checks after
         	// for unterminated numbers or varaibles.
         	var_ref.Append((char)0);
         	// This ensures that a read-ahead of one will
         	// always be successful without additional logic
         	// to check if there is one to read.
         	var_ref.Append((char)0);

         	raw = var_ref.ToString();

         	var_ref.Clear();

         	inside_string = false;
         	inside_number = false;
         	inside_var_ref = false;

         	tmp = 0;

         	for (int x = 0; x < raw.Count(); ++x) {
         		if (raw[x] == 0 && raw[x-1] == 0) {
         			// Preserves the ability to always read ahead
         			// one without additional logic. This should
         			// increase performance and readability.
         			break;
         		}

     			bool is_lowercase = raw[x] >= 'a' && raw[x] <= 'z';
     			bool is_uppercase = raw[x] >= 'A' && raw[x] <= 'Z';
     			bool is_number = raw[x] >= '0' && raw[x] <= '9';
     			bool is_underscore = raw[x] == '_';

         		if (inside_var_ref) {
         			bool is_valid_var_ref = is_lowercase || is_uppercase ||
         									is_number || is_underscore;

         			if (!is_valid_var_ref) {
         				inside_var_ref = false;
         				--x;
	         			linear.Add(new ExpressionPart {
	         				IsVarRef = true,
	         				StringValue = var_ref.ToString(),
	         			});
	         			var_ref.Clear();
         			} else {
	         			var_ref.Append(raw[x]);
	         		}
         		} else if (inside_number) {
         			if (raw[x] != 'x' && !is_number) {
         				// Evaluate the digits now.
         				linear.Add(new ExpressionPart {
         					StringValue = numdigits.ToString(),
         					IsNumber = true,
         				});
         				numdigits.Clear();
         				inside_number = false;
         			} else {
         				// Evaluate the digits later.
         				numdigits.Append(raw[x]);
         			}
         		} else if (inside_string) {
         			if (raw[x] == '"' || raw[x] == 0) {
	 					inside_string = false;
	 					linear.Add(new ExpressionPart {
	 						StringValue = raw.Substring(tmp, x - tmp),
	 						IsString = true
	 					});
	 				}
         		} else if (raw[x] == '"') {
         			if (!inside_string) {
         				inside_string = true;
         				tmp = x + 1;
         			}
         		} else if (raw[x] == ',') {
         			linear.Add(new ExpressionPart {
         				StringValue = ",",
         				IsComma = true
         			});
         		} else if (raw[x] == ' ') {
         			continue;
         		} else if (raw[x] >= '0' && raw[x] <= '9') {
         			inside_number = true;
         			numdigits.Clear();
         			numdigits.Append(raw[x]);
         		} else if (raw[x] == '+') {
         			linear.Add(new ExpressionPart {
         				StringValue = "+",
         				IsAdd = true
         			});
         		} else if (raw[x] == '-') {
         			linear.Add(new ExpressionPart {
         				StringValue = "-",
         				IsSub = true
         			});
         		} else if (raw[x] == '*') {
         			linear.Add(new ExpressionPart {
         				StringValue = "*",
         				IsMul = true
         			});
         		} else if (raw[x] == '/') {
         			linear.Add(new ExpressionPart {
         				StringValue = "/",
         				IsDiv = true
         			});
         		} else if (raw[x] == '%') {
         			linear.Add(new ExpressionPart {
         				StringValue = "%",
         				IsModulus = true
         			});
         		} else if (raw[x] == '(') {
         			linear.Add(new ExpressionPart {
         				StringValue = "(",
         				IsParathesis = true,
         				IsParaOpen = true,
         			});
         		} else if (raw[x] == ')') {
         			linear.Add(new ExpressionPart {
         				StringValue = ")",
         				IsParathesis = true,
         				IsParaClose = true,
         			});
         		} else if (raw[x] == '&') {
         			if (raw[x+1] == '&') {
         				++x;
         				linear.Add(new ExpressionPart {
         					StringValue = "&&",
         					IsLogAnd = true,
         				});
         			} else {
         				linear.Add(new ExpressionPart {
         					StringValue = "&",
         					IsBitAnd = true,
         				});
         			}
         		} else if (raw[x] == '=') {
         			if (raw[x+1] == '=') {
         				linear.Add(new ExpressionPart {
         					StringValue = "==",
         					IsCmpEq = true,
         				});
         			} else {
         				linear.Add(new ExpressionPart {
         					StringValue = "=",
         					IsAssign = true,
         				});
         			}
         		} else if (raw[x] == '|') {
         			if (raw[x+1] == '|') {
         				++x;
         				linear.Add(new ExpressionPart {
         					StringValue = "||",
         					IsLogOr = true,
         				});
         			} else {
         				linear.Add(new ExpressionPart {
         					StringValue = "|",
         					IsBitOr = true,
         				});
         			}
         		} else if (raw[x] == '^') {
         			if (raw[x+1] == '^') {
         				++x;
         				linear.Add(new ExpressionPart {
         					StringValue = "^^",
         					IsLogXor = true,
         				});
         			} else {
         				linear.Add(new ExpressionPart {
         					StringValue = "^",
         					IsBitXor = true,
         				});
         			}
         		} else if (raw[x] == '>') {
         			if (raw[x+1] == '>') {
         				++x;
         				linear.Add(new ExpressionPart {
         					StringValue = ">>",
         					IsShiftRight = true,
         				});
         			} else if (raw[x+1] == '=') {
         				linear.Add(new ExpressionPart {
         					StringValue = ">=",
         					IsCmpEqGr = true
         				});         				
         			} else {
         				linear.Add(new ExpressionPart {
         					StringValue = ">",
         					IsCmpGr = true,
         				});
         			}
         		} else if (raw[x] == '<') {
         			if (raw[x+1] == '<') {
         				++x;
         				linear.Add(new ExpressionPart {
         					StringValue = "<<",
         					IsShiftLeft = true,
         				});
         			} else if (raw[x+1] == '=') {
         				linear.Add(new ExpressionPart {
         					StringValue = "<=",
         					IsCmpEqLs = true
         				});         				
         			} else {
         				linear.Add(new ExpressionPart {
         					StringValue = "<",
         					IsCmpLs = true,
         				});
         			}         		
         		} else {
         			inside_var_ref = true;
         			var_ref.Append(raw[x]);
         		}
         	}
         	
         	// Find all special keywords and convert those to such keyword.
         	for (int x = 0; x < linear.Count; ++x) {
         		ExpressionPart part = linear[x] as ExpressionPart;

         		if (part.IsString) {
         			if (string.Compare(part.StringValue, "new") == 0) {
         				linear[x] = new ExpressionPart {
         					IsNew = true,
         				};
         			} else if (string.Compare(part.StringValue, "as") == 0) {
         				linear[x] = new ExpressionPart {
         					IsCast = true,
         				};
         			}
         		}
         	}

         	// Find all variable names with a immediate trailing open parathesis
         	// and call these function/method invocations.
         	//
         	//		The InvokeStmt type can parse these groupings.
         	//
         	// Also, everything is going to be kept linear until the final phase
         	// in which a tree will be created and ultimately returned from this
         	// method.
         	for (int x = 0; x < linear.Count - 1; ++x) {
         		ExpressionPart part0 = linear[x] as ExpressionPart;
         		ExpressionPart part1 = linear[x+1] as ExpressionPart;

         		if (part0.IsParaOpen) {
         			Expression expstmt = new Expression();

         			int y = x + 1;
         			for (; y < linear.Count; ++y) {
         				ExpressionPart part = linear[y] as ExpressionPart;
         				if (part.IsParaClose) {
         					break;
         				} else {
         					expstmt.Body.Add(part);
         				}
         			}

         			linear.RemoveRange(x, y - x + 1);
         			linear.Insert(x, expstmt);
         		}

         		if (part0.IsVarRef && part1.IsParaOpen) {
         			// Look for closing parathesis.
         			for (int y = x + 1; y < linear.Count; ++y) {
         				ExpressionPart part = linear[y] as ExpressionPart;
         				if (part.IsParaClose) {
         					// The problem is that I use very specific tokens
         					// above in order to parse out an expression, but
         					// InvokeStmt has logic that works on a string. It
         					// would be silly to reconvert back into a string
         					// only to have this called again to deal with this
         					// particular case. Therefore, the InvokeStmt is
         					// going to be built in-place right here without
         					// calling its parse method.
         					string fn_name = part0.StringValue;
         					// The arguments are going to be of the type
         					// Expression. I guess the Stmt (statement)
         					// part is debatable, but it will blend in with
         					// the current naming scheme for the AST.
         					List<IAst> arguments = new List<IAst>();
         					Expression expstmt = new Expression();

         					for (int z = x + 2; z < y; ++z) {
         						ExpressionPart _part = linear[z] as ExpressionPart;
         						if (_part.IsComma) {
         							arguments.Add(expstmt);
         							expstmt = new Expression();
         						} else {
         							expstmt.Body.Add(_part);
         						}
         					}

         					if (expstmt.Body.Count > 0) {
         						arguments.Add(expstmt);
         					}

         					InvokeStmt invstmt = new InvokeStmt();

         					invstmt.Params = arguments;
         					invstmt.Path = fn_name;

         					// This will cause `x` to start right after
         					// the newly inserted `expstmt` AST node.
         					linear.RemoveRange(x, y - x + 1);
         					linear.Insert(x, invstmt);
         					break;
         				}
         			}
         		}
         	}

         	this.Body = linear;
         	return this;
        }
    }
}


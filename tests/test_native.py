import json
from pathlib import Path
import unittest
from backend.compiler import Compiler
from backend.runner import QemuRunner
from backend.service import ExecutionService


VALID = [
    ('lexer_comments', '/* comentario\n múltiple */ fn main(){// línea\n println!("á\\nβ");}', ['á', 'β']),
    ('defaults', 'fn main(){let a:i32;let b:f64;let c:bool;let d:String;println!("{} {} {} {}",a,b,c,d);}', ['0 0.0 false ']),
    ('variables', 'fn main(){let x=1;let x=2;{let x=3;println!(x);}let mut y=x;y+=5;y*=2;y-=1;y/=3;y%=3;println!(y);println!(x);}', ['3','1','2']),
    ('integer_arithmetic', 'fn main(){println!("{} {} {} {} {}",8+2,8-2,8*2,9/2,9%2);println!(-9/2);println!(-9%2);}', ['10 6 16 4 1','-4','-1']),
    ('float_arithmetic', 'fn main(){println!("{} {} {} {} {}",1+2.5,5.5-2,2*1.5,5.0/2,5.5%2);}', ['3.5 3.5 3.0 2.5 1.5']),
    ('relations', 'fn main(){println!("{} {} {} {} {} {}",1==1.0,1!=2,3>2.0,3>=3,2<3,2<=2);println!("a"<"b");println!(false<true);println!(65==\'A\');}', ['true true true true true true','true','true','true']),
    ('logic', 'fn side()->bool{println!("side");return true;}fn main(){println!(false&&side());println!(true||side());println!(!false&&true);}', ['false','true','true']),
    ('if_else', 'fn main(){if false{println!(1);}else if true{println!(2);}else{println!(3);}}', ['2']),
    ('while', 'fn main(){let mut i=0;while i<5{i+=1;if i==2{continue;}if i==4{break;}println!(i);}}', ['1','3']),
    ('loop_labels', "fn main(){let mut i=0;'outer:loop{i+=1;loop{if i<3{continue 'outer;}break 'outer;}}println!(i);}", ['3']),
    ('match', 'fn main(){let n=2;match n{1=>println!("uno"),2=>{println!("dos");},_=>println!("otro"),}}', ['dos']),
    ('match_float', 'fn main(){let n=2.5;match n{1.0=>println!(1),2.5=>println!(2),_=>println!(3),}}', ['2']),
    ('match_string', 'fn main(){match "b"{"a"=>println!(1),"b"=>println!(2),_=>println!(3),}}', ['2']),
    ('functions', 'fn add(a:i32,b:i32)->i32{return a+b;}fn hello(s:String){println!("Hola {}",s);}fn main(){hello("Ana");println!(add(10,20));}', ['Hola Ana','30']),
    ('recursion', 'fn fib(n:i32)->i32{if n<2{return n;}return fib(n-1)+fib(n-2);}fn main(){println!(fib(10));}', ['55']),
    ('float_abi', 'fn sum(a:f64,b:i32,c:f64)->f64{return a+b+c;}fn main(){println!(sum(1.5,2,3.25));}', ['6.75']),
    ('int_to_float_return', 'fn f()->f64{return 7;}fn main(){println!(f());}', ['7.0']),
    ('array', 'fn main(){let mut a:[i32;3]=[1,2,3];a[1]+=5;println!(a);println!(a.len());}', ['[1, 7, 3]','3']),
    ('array_repeat', 'fn value()->i32{println!("once");return 3;}fn main(){let a=[value();3];println!(a);}', ['once','[3, 3, 3]']),
    ('matrix', 'fn main(){let mut a:[[i32;3];2]=[[1,2,3],[4,5,6]];a[1][2]=7;println!(a);println!(a[1][2]);}', ['[[1, 2, 3], [4, 5, 7]]','7']),
    ('cube', 'fn main(){let a=[[[1,2],[3,4]],[[5,6],[7,8]]];println!(a[1][0][1]);}', ['6']),
    ('subarray_assignment', 'fn main(){let mut a=[[1,2],[3,4]];a[0]=[8,9];println!(a);}', ['[[8, 9], [3, 4]]']),
    ('slices', 'fn main(){let mut a=[10,20,30,40];let b=&a[1..3];a[1]=99;println!(b);println!(b.len());}', ['[99, 30]','2']),
    ('array_functions', 'fn sum(a:[i32;3])->i32{return a[0]+a[1]+a[2];}fn main(){println!(sum([1,2,3]));}', ['6']),
    ('array_return', 'fn pair()->[i32;2]{return [1,2];}fn main(){println!(pair());}', ['[1, 2]']),
    ('float_array_return', 'fn f()->[f64;2]{return [1,2];}fn main(){println!(f());}', ['[1.0, 2.0]']),
    ('float_array_assignment', 'fn main(){let mut a:[f64;2]=[1,2];a=[3,4];println!(a);}', ['[3.0, 4.0]']),
    ('float_array', 'fn main(){let a:[f64;2]=[1,2];println!(a);println!(a.contains(2));}', ['[1.0, 2.0]','true']),
    ('strings', 'fn main(){let a=String::from("Hola");let mut b=String::new();b+="Mundo";println!(a+" "+b);println!("ab"*3);println!(2*"xy");}', ['Hola Mundo','ababab','xyxy']),
    ('string_escapes', 'fn main(){println!("a\\t\\\"b\\\"\\\\c");println!(r"a\\nb");}', ['a\t"b"\\c','a\\nb']),
    ('string_methods', 'fn main(){let s="Hola Mundo";println!(s.len());println!(s.contains("Mundo"));println!(s.replace("Mundo","Rust"));println!(s.split(" "));println!(s.to_uppercase());println!(s.to_lowercase());}', ['10','true','Hola Rust','["Hola", "Mundo"]','HOLA MUNDO','hola mundo']),
    ('unicode', 'fn main(){let s="niño β";println!(s.len());println!(s.contains(\'ñ\'));println!(s.chars());println!(\'😀\');}', ['6','true','[n, i, ñ, o,  , β]','😀']),
    ('string_construction', 'fn main(){println!(String::from(12));println!(String::from(1.5));println!(String::from(true));println!(String::from(\'A\'));}', ['12','1.5','true','A']),
    ('natives', 'fn main(){let mut a=[1,2,3];let b=a.clone();a.reverse();println!(a);println!(b);println!(a.contains(2));println!(typeof(a));println!(abs(-5));println!(sqrt(9));let r=random(1,3);println!(r>=1&&r<=3);}', ['[3, 2, 1]','[1, 2, 3]','true','[i32; 3]','5','3.0','true']),
    ('empty_typed_array', 'fn main(){let a:[i32;0]=[];println!(a);}', ['[]']),
    ('matrix_return', 'fn f()->[[i32;2];2]{return [[1,2],[3,4]];}fn main(){println!(f()[1][0]);}', ['3']),
    ('matrix_float', 'fn main(){let a:[[f64;2];2]=[[1,2],[3,4]];println!(a);}', ['[[1.0, 2.0], [3.0, 4.0]]']),
    ('integer_limits', 'fn main(){println!(-2147483648);println!(2147483647+1);}', ['-2147483648','-2147483648']),
    ('strings_array', 'fn main(){let a=["uno","dos"];println!(a.contains("dos"));println!(a[1]);}', ['true','dos']),
    ('match_transfer', 'fn main(){let mut i=0;while i<3{i+=1;match i{1=>continue,2=>println!(i),_=>break,}}println!(i);}', ['2','3']),
]

INVALID = [
    ('lexical', 'fn main(){let a=@1;}'),
    ('comment_unclosed', 'fn main(){} /* abierto'),
    ('syntax_semicolon', 'fn main(){let a=1 println!(a);}'),
    ('syntax_brace', 'fn main(){println!(1);'),
    ('missing_main', 'fn other(){}'),
    ('duplicate_main', 'fn main(){}fn main(){}'),
    ('duplicate_function', 'fn f(){}fn f(){}fn main(){}'),
    ('main_parameters', 'fn main(x:i32){}'),
    ('undeclared', 'fn main(){println!(x);}'),
    ('scope', 'fn main(){{let x=1;}println!(x);}'),
    ('immutability', 'fn main(){let x=1;x=2;}'),
    ('array_immutability', 'fn main(){let a=[1,2];a[0]=3;}'),
    ('type_assignment', 'fn main(){let mut x=1;x="bad";}'),
    ('bad_condition', 'fn main(){if 1{println!(1);}}'),
    ('unreachable_error', 'fn main(){if false{println!(missing);}}'),
    ('unused_function_error', 'fn bad(){println!(missing);}fn main(){}'),
    ('uninitialized', 'fn main(){let c:char;println!(c);}'),
    ('uninferred', 'fn main(){let x;}'),
    ('argument_count', 'fn f(x:i32){}fn main(){f();}'),
    ('argument_type', 'fn f(x:i32){}fn main(){f("bad");}'),
    ('unknown_function', 'fn main(){missing();}'),
    ('duplicate_parameters', 'fn f(x:i32,x:i32){}fn main(){}'),
    ('return_type', 'fn f()->i32{return "bad";}fn main(){}'),
    ('return_path', 'fn f(x:bool)->i32{if x{return 1;}}fn main(){}'),
    ('main_return', 'fn main(){return 1;}'),
    ('break', 'fn main(){break;}'),
    ('label', "fn main(){loop{break 'missing;}}"),
    ('logic_types', 'fn main(){println!(1&&true);}'),
    ('arithmetic_types', 'fn main(){println!(1+"x");}'),
    ('array_size', 'fn main(){let a:[i32;3]=[1,2];}'),
    ('array_shape', 'fn main(){let a=[[1,2],[3]];}'),
    ('array_element', 'fn main(){let a=[1,"bad"];}'),
    ('array_negative_constant', 'fn main(){let a=[1,2];println!(a[-1]);}'),
    ('array_bounds', 'fn main(){let a=[1,2];println!(a[2]);}'),
    ('array_index_type', 'fn main(){let a=[1,2];println!(a[true]);}'),
    ('slice_bounds', 'fn main(){let a=[1,2];let b=&a[0..3];}'),
    ('format', 'fn main(){println!("{} {}",1);}'),
    ('integer_range', 'fn main(){println!(2147483648);}'),
    ('native_type', 'fn main(){println!(1.len());}'),
    ('void_parameter', 'fn f(a:void){}fn main(){}'),
    ('huge_array', 'fn main(){let a:[i32;1000000000]=[0;1000000000];}'),
    ('bad_char_escape', r"fn main(){println!('\q');}"),
    ('native_count', 'fn main(){println!("x".replace("a"));}'),
    ('reverse_mutability', 'fn main(){let a=[1,2];a.reverse();}'),
]

RUNTIME_ERRORS = [
    ('division_zero', 'fn main(){let z=0;println!(1/z);}'),
    ('float_zero', 'fn main(){let z=0.0;println!(1.0/z);}'),
    ('dynamic_bounds', 'fn main(){let a=[1,2];let i=3;println!(a[i]);}'),
    ('negative_index', 'fn main(){let a=[1,2];let i=-1;println!(a[i]);}'),
    ('negative_repeat', 'fn main(){println!("a" * -2);}'),
    ('random_range', 'fn main(){println!(random(2,1));}'),
    ('negative_sqrt', 'fn main(){println!(sqrt(-1));}'),
]


class NativeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.results = []
        cls.runner = QemuRunner()
        if not cls.runner.available():
            raise unittest.SkipTest('Se requieren GNU AArch64, QEMU y prlimit')

    def test_valid_programs(self):
        for label, source, expected in VALID:
            with self.subTest(label=label):
                compiled = Compiler().compile(source)
                self.assertEqual(compiled['errors'], [], label)
                execution = self.runner.run(compiled['assembly'])
                self.results.append((label, source, expected, execution['stdout'].splitlines(), execution['exit_code']))
                self.assertEqual(execution['exit_code'], 0, execution['stderr'])
                self.assertEqual(execution['stdout'].splitlines(), expected)
                self.assertEqual(len(execution['commands']), 4)
                self.assertEqual(execution['architecture'], 'AArch64')

    def test_runtime_errors(self):
        for label, source in RUNTIME_ERRORS:
            with self.subTest(label=label):
                compiled = Compiler().compile(source)
                self.assertEqual(compiled['errors'], [])
                result = self.runner.run(compiled['assembly'])
                self.assertNotEqual(result['exit_code'], 0)
                self.assertIn('[Ejecución]', result['stderr'])

    def test_timeout(self):
        compiled = Compiler().compile('fn main(){loop{}}')
        result = QemuRunner(timeout=0.2).run(compiled['assembly'])
        self.assertIsNone(result['exit_code'])
        self.assertIn('Tiempo límite', result['stderr'])

    def test_output_limit(self):
        compiled = Compiler().compile('fn main(){let mut i=0;while i<200000{println!("salida acotada del programa");i+=1;}}')
        result = self.runner.run(compiled['assembly'])
        self.assertNotEqual(result['exit_code'], 0)
        self.assertLessEqual(len(result['stdout'].encode()), 1048576)

    def test_stack_arguments(self):
        for kind in ('i32', 'f64'):
            params = ','.join(f'p{i}:{kind}' for i in range(10))
            source = f'fn sum({params})->{kind}{{return '+ '+'.join(f'p{i}' for i in range(10)) + ';}fn main(){println!(sum(' + ','.join(str(i) for i in range(10)) + '));}'
            compiled = Compiler().compile(source)
            self.assertEqual(compiled['errors'], [])
            result = self.runner.run(compiled['assembly'])
            self.assertEqual(result['exit_code'], 0, result['stderr'])
            self.assertEqual(result['stdout'].strip(), '45.0' if kind == 'f64' else '45')

    @classmethod
    def tearDownClass(cls):
        Path('/tmp/oxigennative-test-results.json').write_text(json.dumps(cls.results, ensure_ascii=False, indent=2))


class SemanticTests(unittest.TestCase):
    def test_negative_programs(self):
        for label, source in INVALID:
            with self.subTest(label=label):
                result = Compiler().compile(source)
                self.assertFalse(result['success'])
                self.assertTrue(result['errors'])
                self.assertEqual(result['assembly'], '')

    def test_error_accumulation(self):
        result = Compiler().compile('fn main(){println!(a);println!(b);}')
        self.assertEqual(len(result['errors']), 2)
        self.assertTrue(all(error['fragment'] for error in result['errors']))

    def test_short_circuit_checks_rhs(self):
        self.assertFalse(Compiler().compile('fn main(){println!(false&&missing);}')['success'])


if __name__ == '__main__':
    unittest.main()

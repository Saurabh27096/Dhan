package ststic_keyword;



public class static_method {

    public static void main(String[] args) {
        Q q = new Q();
        System.out.println(q.s2());
        System.out.println(Q.s1());


    }

    static{
        System.out.println("I am static block");
    }

}

class  Q{
    public static String s1(){    // can't access s1 using object of the class
        return "I am function s1";
    }
    public String s2(){          // can't access s2 using class name
        return "I am function s2";
    }
}

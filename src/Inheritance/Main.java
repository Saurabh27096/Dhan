package Inheritance;

public class Main {
    public static void main(String[] args) {
        Teacher teacher = new Teacher();
        teacher.name = "saurabh";
        teacher.eat();
        teacher.teach();

        Teacher t = new Teacher();
        t.name = "yadav";
        t.teach();
    }
}

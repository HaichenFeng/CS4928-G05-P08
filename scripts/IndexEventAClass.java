import com.github.javaparser.*;
import com.github.javaparser.ast.body.*;
import com.google.gson.*;
import java.nio.file.*;
public class IndexEventAClass {
 public static void main(String[] a)throws Exception {
  StaticJavaParser.getParserConfiguration().setLanguageLevel(ParserConfiguration.LanguageLevel.BLEEDING_EDGE);
  var cu=StaticJavaParser.parse(Paths.get(a[0]));
  var names=new java.util.ArrayList<String>(); for(TypeDeclaration<?> t:cu.findAll(TypeDeclaration.class)){String name=t.getFullyQualifiedName().orElse("");if(!name.isEmpty())names.add(name);}
  Files.writeString(Paths.get(a[1]),new Gson().toJson(names));
 }
}
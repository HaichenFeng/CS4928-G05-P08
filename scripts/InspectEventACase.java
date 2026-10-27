import com.github.javaparser.*;
import com.github.javaparser.ast.*;
import com.github.javaparser.ast.body.*;
import com.github.javaparser.ast.expr.*;
import com.google.gson.*;
import java.nio.file.*;
import java.util.*;

/** M2 JavaParser facts, with prospective Rule 4 overload selection. No gold input. */
public class InspectEventACase {
  static Map<String,Object> variable(VariableDeclarator v) {
    return Map.of("name",v.getNameAsString(),"type",v.getTypeAsString(),"line",v.getBegin().get().line);
  }
  static List<String> split(String s) {
    List<String> out=new ArrayList<>(); int depth=0,start=0;
    for(int i=0;i<s.length();i++) {
      char c=s.charAt(i); if(c=='<')depth++; if(c=='>')depth--;
      if(c==',' && depth==0){out.add(s.substring(start,i).trim());start=i+1;}
    }
    if(!s.trim().isEmpty())out.add(s.substring(start).trim()); return out;
  }
  static String norm(String s){return s.replaceAll("\s+","").replace("...","[]");}
  public static void main(String[] args) throws Exception {
    String host=args[1], signature=args[2];
    String methodName=signature.substring(0,signature.indexOf('(')).replaceAll(".* ","");
    List<String> expectedTypes=new ArrayList<>();
    for(String p:split(signature.substring(signature.indexOf('(')+1,signature.lastIndexOf(')')))) {
      int space=p.indexOf(' '); if(space<0)throw new IllegalArgumentException("Unrecognised dataset parameter: "+p);
      expectedTypes.add(norm(p.substring(space+1)));
    }
    StaticJavaParser.getParserConfiguration().setLanguageLevel(ParserConfiguration.LanguageLevel.BLEEDING_EDGE);
    CompilationUnit cu=StaticJavaParser.parse(Paths.get(args[0]));
    var classes=cu.findAll(ClassOrInterfaceDeclaration.class).stream()
      .filter(c->c.getFullyQualifiedName().orElse("").equals(host)).toList();
    if(classes.size()!=1)throw new IllegalStateException("Host selection: "+host+" "+classes.size());
    var cls=classes.get(0); var named=cls.getMethodsByName(methodName);
    var selected=named.size()==1 ? named : named.stream().filter(m->
      m.getParameters().stream().map(p->norm(p.getTypeAsString()+(p.isVarArgs()?"[]":""))).toList().equals(expectedTypes)).toList();
    if(selected.size()!=1)throw new IllegalStateException("Rule4 method selection: "+methodName+" named="+named.size()+" matched="+selected.size());
    var method=selected.get(0); Map<String,Object> result=new LinkedHashMap<>();
    result.put("host",host); result.put("package",cu.getPackageDeclaration().get().getNameAsString());
    result.put("imports",cu.getImports().stream().map(Object::toString).toList());
    result.put("fields",cls.getFields().stream().flatMap(f->f.getVariables().stream()).map(InspectEventACase::variable).toList());
    result.put("parameters",method.getParameters().stream().map(p->Map.of("name",p.getNameAsString(),"type",p.getTypeAsString(),"line",p.getBegin().get().line)).toList());
    result.put("locals",method.findAll(VariableDeclarator.class).stream().map(InspectEventACase::variable).toList());
    result.put("method_source",method.toString()); result.put("method_line",method.getBegin().get().line);
    result.put("actual_return_type",method.getTypeAsString()); result.put("method_name",methodName);
    result.put("rule4_selection",named.size()==1 ? "unique name" : "unique parameter count/types");
    result.put("frozen_parameter_types",expectedTypes);
    List<Object> accesses=new ArrayList<>();
    for(MethodCallExpr call:method.findAll(MethodCallExpr.class))
      if(call.getScope().isPresent())accesses.add(Map.of("kind","call","scope",call.getScope().get().toString(),"member",call.getNameAsString(),"line",call.getBegin().get().line));
    for(FieldAccessExpr access:method.findAll(FieldAccessExpr.class))
      accesses.add(Map.of("kind","field","scope",access.getScope().toString(),"member",access.getNameAsString(),"line",access.getBegin().get().line));
    result.put("member_accesses",accesses);
    Files.writeString(Paths.get(args[3]),new GsonBuilder().setPrettyPrinting().disableHtmlEscaping().create().toJson(result));
  }
}
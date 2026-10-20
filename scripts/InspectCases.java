import com.github.javaparser.*;
import com.github.javaparser.ast.*;
import com.github.javaparser.ast.body.*;
import com.github.javaparser.ast.expr.*;
import com.google.gson.*;
import java.nio.file.*;
import java.util.*;

public class InspectCases {
  static Map<String,Object> variable(VariableDeclarator v) {
    return Map.of("name",v.getNameAsString(),"type",v.getTypeAsString(),"line",v.getBegin().get().line);
  }
  public static void main(String[] args) throws Exception {
    Path root=Paths.get(args[0]);
    Gson gson=new GsonBuilder().setPrettyPrinting().disableHtmlEscaping().create();
    for (Path folder:Files.list(root.resolve("outputs/requests")).sorted().toList()) {
      if (!Files.isDirectory(folder)) continue;
      JsonObject input=JsonParser.parseString(Files.readString(folder.resolve("input_record.json"))).getAsJsonObject();
      String host=input.get("host_class").getAsString();
      String signature=input.get("method_signature_from_frozen_sample").getAsString();
      String methodName=signature.substring(0,signature.indexOf('(')).replaceAll(".* ","");
      CompilationUnit cu=StaticJavaParser.parse(folder.resolve("host.java"));
      var classes=cu.findAll(ClassOrInterfaceDeclaration.class).stream()
        .filter(c->c.getFullyQualifiedName().orElse("").equals(host)).toList();
      if(classes.size()!=1)throw new IllegalStateException("Host selection: "+host+" "+classes.size());
      var cls=classes.get(0);
      var methods=cls.getMethodsByName(methodName);
      if(methods.size()!=1)throw new IllegalStateException("Method selection: "+signature+" "+methods.size());
      var method=methods.get(0);
      Map<String,Object> result=new LinkedHashMap<>();
      result.put("case_id",input.get("case_id").getAsInt());
      result.put("host",host);
      result.put("package",cu.getPackageDeclaration().get().getNameAsString());
      result.put("imports",cu.getImports().stream().map(Object::toString).toList());
      result.put("fields",cls.getFields().stream().flatMap(f->f.getVariables().stream()).map(InspectCases::variable).toList());
      result.put("parameters",method.getParameters().stream().map(p->Map.of("name",p.getNameAsString(),"type",p.getTypeAsString(),"line",p.getBegin().get().line)).toList());
      result.put("locals",method.findAll(VariableDeclarator.class).stream().map(InspectCases::variable).toList());
      result.put("method_source",method.toString());
      result.put("method_line",method.getBegin().get().line);
      List<Object> accesses=new ArrayList<>();
      for(MethodCallExpr call:method.findAll(MethodCallExpr.class)) {
        if(call.getScope().isPresent()) accesses.add(Map.of("kind","call","scope",call.getScope().get().toString(),"member",call.getNameAsString(),"line",call.getBegin().get().line));
      }
      for(FieldAccessExpr access:method.findAll(FieldAccessExpr.class)) accesses.add(Map.of("kind","field","scope",access.getScope().toString(),"member",access.getNameAsString(),"line",access.getBegin().get().line));
      result.put("member_accesses",accesses);
      Files.writeString(root.resolve("outputs/evaluation/"+input.get("case_id").getAsString()+"_ast.json"),gson.toJson(result));
      System.out.println("Parsed case "+input.get("case_id")+": "+host+"."+methodName);
    }
  }
}

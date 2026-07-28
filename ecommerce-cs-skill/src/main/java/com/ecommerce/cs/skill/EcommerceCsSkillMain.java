package com.ecommerce.cs.skill;

import com.ecommerce.cs.compliance.ComplianceReport;
import com.ecommerce.cs.llm.LlmException;
import com.ecommerce.cs.llm.LlmInspectionResult;
import com.ecommerce.cs.model.AgentReply;
import com.ecommerce.cs.scenario.TrackingScenario;
import com.ecommerce.cs.web.DialogueDemoServer;

import java.util.List;

/**
 * 命令行入口：模板模拟、真实 LLM 质检、HTTP 演示服务。
 *
 * <pre>
 *   ./mvnw -q -DskipTests package
 *   java -jar target/ecommerce-cs-skill-1.0.0-SNAPSHOT.jar --list
 *   java -jar target/ecommerce-cs-skill-1.0.0-SNAPSHOT.jar --regression
 *   java -jar target/ecommerce-cs-skill-1.0.0-SNAPSHOT.jar --llm S01_IN_TRANSIT
 *   java -jar target/ecommerce-cs-skill-1.0.0-SNAPSHOT.jar --llm-regression
 *   java -jar target/ecommerce-cs-skill-1.0.0-SNAPSHOT.jar --serve 8080
 * </pre>
 */
public final class EcommerceCsSkillMain {

    private EcommerceCsSkillMain() {
    }

    public static void main(String[] args) throws Exception {
        if (args.length > 0 && "--serve".equals(args[0])) {
            int port = 8080;
            if (args.length > 1) {
                port = Integer.parseInt(args[1]);
            } else if (System.getenv("PORT") != null && !System.getenv("PORT").isBlank()) {
                port = Integer.parseInt(System.getenv("PORT"));
            }
            new DialogueDemoServer(port).start();
            Thread.currentThread().join();
            return;
        }

        if (args.length > 0 && "--llm".equals(args[0])) {
            String scenarioId = args.length > 1 ? args[1] : "S01_IN_TRANSIT";
            runLlmOnce(scenarioId);
            return;
        }

        if (args.length > 0 && "--llm-regression".equals(args[0])) {
            runLlmRegression();
            return;
        }

        EcommerceOrderTrackingSkill skill = new EcommerceOrderTrackingSkill();

        if (args.length > 0 && "--regression".equals(args[0])) {
            runRegression(skill);
            return;
        }

        if (args.length > 0 && "--list".equals(args[0])) {
            skill.catalog().all().stream()
                    .sorted((a, b) -> a.id().compareTo(b.id()))
                    .forEach(s -> System.out.println(s.id() + " | " + s.name() + " | " + s.description()));
            return;
        }

        if (args.length > 0 && "--help".equals(args[0])) {
            printHelp();
            return;
        }

        String scenarioId = args.length > 0 ? args[0] : "S01_IN_TRANSIT";
        TrackingScenario scenario = skill.catalog().require(scenarioId);

        System.out.println("======== 场景 ========");
        scenario.summaryLines().forEach(System.out::println);

        AgentReply compliant = skill.simulateCompliantReply(scenarioId);
        ComplianceReport okReport = skill.evaluate(scenario, compliant);
        System.out.println("\n======== 合规模拟回复 ========");
        System.out.println(compliant.content());
        System.out.println("\n-------- 规范检测 --------");
        System.out.print(okReport.render());

        AgentReply bad = skill.simulateNonCompliantReply(scenarioId);
        ComplianceReport badReport = skill.evaluate(scenario, bad);
        System.out.println("\n======== 违规样例回复 ========");
        System.out.println(bad.content());
        System.out.println("\n-------- 规范检测 --------");
        System.out.print(badReport.render());
    }

    private static void runLlmOnce(String scenarioId) {
        EcommerceOrderTrackingSkill skill = EcommerceOrderTrackingSkill.withLlmFromEnv();
        System.out.println("调用真实 LLM 并质检场景: " + scenarioId);
        try {
            LlmInspectionResult result = skill.simulateWithLlmAndInspect(scenarioId);
            System.out.print(result.render());
            if (!result.passed()) {
                System.exit(2);
            }
        } catch (LlmException ex) {
            System.err.println("LLM 调用失败: " + ex.getMessage());
            System.err.println("请检查 LLM_BASE_URL / LLM_API_KEY / LLM_MODEL，参见 DEPLOY.md");
            System.exit(1);
        }
    }

    private static void runLlmRegression() {
        EcommerceOrderTrackingSkill skill = EcommerceOrderTrackingSkill.withLlmFromEnv();
        System.out.println("======== 真实 LLM 全场景质检 ========");
        int pass = 0;
        List<LlmInspectionResult> results;
        try {
            results = skill.runLlmInspectionRegression();
        } catch (LlmException ex) {
            System.err.println("LLM 调用失败: " + ex.getMessage());
            System.exit(1);
            return;
        }
        for (LlmInspectionResult result : results) {
            System.out.print(result.render());
            System.out.println();
            if (result.passed()) {
                pass++;
            }
        }
        System.out.println("LLM 质检通过: " + pass + "/" + results.size());
        if (pass != results.size()) {
            System.exit(2);
        }
    }

    private static void runRegression(EcommerceOrderTrackingSkill skill) {
        System.out.println("======== 合规模拟回归 ========");
        List<ComplianceReport> ok = skill.runCompliantRegression();
        int pass = 0;
        for (ComplianceReport report : ok) {
            System.out.print(report.render());
            if (report.allPassed()) {
                pass++;
            }
            System.out.println();
        }
        System.out.println("合规通过: " + pass + "/" + ok.size());

        System.out.println("======== 违规样例应被检出 ========");
        List<ComplianceReport> bad = skill.runNonCompliantDetection();
        int detected = 0;
        for (ComplianceReport report : bad) {
            System.out.print(report.render());
            if (!report.allPassed()) {
                detected++;
            }
            System.out.println();
        }
        System.out.println("成功检出违规: " + detected + "/" + bad.size());
    }

    private static void printHelp() {
        System.out.println("""
                用法:
                  --list                     列出场景
                  --regression               规则模板回归（无需 LLM）
                  --llm [场景ID]             调用真实 LLM 生成回复并质检
                  --llm-regression           全部场景走真实 LLM + 质检
                  --serve [端口]             启动 Web 演示（默认 8080）
                  <场景ID>                   模板合规/违规对照演示
                  --help                     帮助

                环境变量:
                  LLM_BASE_URL   OpenAI 兼容地址，如 http://127.0.0.1:11434/v1
                  LLM_API_KEY    Bearer Token（本地可填 local）
                  LLM_MODEL      模型名，如 qwen2.5:7b
                """);
    }
}

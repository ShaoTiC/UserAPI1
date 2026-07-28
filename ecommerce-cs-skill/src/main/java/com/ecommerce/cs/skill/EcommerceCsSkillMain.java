package com.ecommerce.cs.skill;

import com.ecommerce.cs.compliance.ComplianceReport;
import com.ecommerce.cs.model.AgentReply;
import com.ecommerce.cs.scenario.TrackingScenario;

import java.util.List;

/**
 * 命令行入口：演示场景对话与规范检测。
 *
 * <pre>
 *   mvn -q -DskipTests package
 *   java -jar target/ecommerce-cs-skill-1.0.0-SNAPSHOT.jar
 *   java -jar target/ecommerce-cs-skill-1.0.0-SNAPSHOT.jar S01_IN_TRANSIT
 *   java -jar target/ecommerce-cs-skill-1.0.0-SNAPSHOT.jar --regression
 * </pre>
 */
public final class EcommerceCsSkillMain {

    private EcommerceCsSkillMain() {
    }

    public static void main(String[] args) {
        EcommerceOrderTrackingSkill skill = new EcommerceOrderTrackingSkill();

        if (args.length > 0 && "--regression".equals(args[0])) {
            runRegression(skill);
            return;
        }

        if (args.length > 0 && "--list".equals(args[0])) {
            skill.catalog().all().forEach(s ->
                    System.out.println(s.id() + " | " + s.name() + " | " + s.description()));
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
}

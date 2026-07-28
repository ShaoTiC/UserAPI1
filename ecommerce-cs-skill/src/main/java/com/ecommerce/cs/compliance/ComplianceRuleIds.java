package com.ecommerce.cs.compliance;

/**
 * 电商 AI 客服订单进度回复规范编码。
 * <p>
 * 说明：以下规范为常见平台客服服务质量基线的可机检近似，
 * 并非某一具体平台的官方合规原文；可按业务方规范表扩展。
 */
public final class ComplianceRuleIds {
    private ComplianceRuleIds() {
    }

    /** 未提供订单号时，必须先索取订单号，不得臆测。 */
    public static final String ORDER_ID_REQUIRED = "ORDER_ID_REQUIRED";

    /** 订单查无结果时，须明确告知并引导核对，不得编造进度。 */
    public static final String ORDER_NOT_FOUND_HANDLING = "ORDER_NOT_FOUND_HANDLING";

    /** 回复中的状态表述须与订单事实一致。 */
    public static final String STATUS_ACCURACY = "STATUS_ACCURACY";

    /** 已发货及之后状态须给出承运商与运单号。 */
    public static final String TRACKING_COMPLETENESS = "TRACKING_COMPLETENESS";

    /** 不得捏造不存在的物流节点或虚假到达时间。 */
    public static final String NO_FABRICATION = "NO_FABRICATION";

    /** 收件人手机、详细地址等须脱敏展示。 */
    public static final String PRIVACY_MASKING = "PRIVACY_MASKING";

    /** 语气礼貌专业，含问候/致谢/致歉等基本礼仪。 */
    public static final String POLITENESS = "POLITENESS";

    /** 须给出与当前状态匹配的可执行下一步建议。 */
    public static final String ACTIONABLE_NEXT_STEP = "ACTIONABLE_NEXT_STEP";

    /** 异常/超时场景须说明原因或现状。 */
    public static final String EXCEPTION_HANDLING = "EXCEPTION_HANDLING";

    /** 异常场景须提供催办、改约、转人工等升级路径。 */
    public static final String ESCALATION_PATH = "ESCALATION_PATH";

    /** 不得在信息不足时做出确定到货承诺。 */
    public static final String NO_OVERPROMISE = "NO_OVERPROMISE";
}

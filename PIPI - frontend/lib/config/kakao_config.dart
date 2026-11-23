/// 카카오 SDK 네이티브 앱 키 설정 관리
///
/// [보안 주의사항]:
/// - 클라이언트는 오직 Kakao Developers에서 발급받은 '네이티브 앱 키'만 사용합니다.
/// - REST API 키나 Admin 키는 절대로 클라이언트 코드에 포함해서는 안 되며,
///   백엔드 서버에서만 사용됩니다.
class KakaoConfig {
  KakaoConfig._();

  /// 카카오 네이티브 앱 키
  ///
  /// 빌드 또는 실행 시:
  ///   flutter run --dart-define=KAKAO_NATIVE_APP_KEY=실제_네이티브_앱_키
  /// 형태로 안전하게 주입할 수 있으며,
  /// 미지정 시 아래 기본 플레이스홀더를 사용합니다.
  static const String nativeAppKey = String.fromEnvironment(
    'KAKAO_NATIVE_APP_KEY',
    defaultValue: '768138760b29ce3818e6e5cb87e07a38', // 카카오 디벨로퍼스 네이티브 앱 키
  );
}

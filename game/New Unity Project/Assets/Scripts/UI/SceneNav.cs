using MP1.Core;
using UnityEngine;
using UnityEngine.SceneManagement;

namespace MP1.UI
{
    /// <summary>
    /// Back navigation for a screen: the visible Back button calls <see cref="GoBack"/>, and Esc does the same
    /// (never during an IME composition). F2 toggles reduced motion. <c>backScene</c> is set per screen so later
    /// production screens can follow the documented user flow instead of always returning to the main menu.
    /// </summary>
    public class SceneNav : MonoBehaviour
    {
        public const string MainMenu = "MainMenu";
        [SerializeField] bool escapeToMenu = true;
        [SerializeField] string backScene = MainMenu;

        public string BackScene => backScene;
        public void SetBack(string scene) => backScene = scene;

        void Update()
        {
            if (Input.GetKeyDown(KeyCode.F2)) MotionSettings.Reduced = !MotionSettings.Reduced;
            if (escapeToMenu && Input.GetKeyDown(KeyCode.Escape) && ImeGate.ShortcutAllowed(Input.compositionString))
                GoBack();
        }

        public void GoBack() => SceneManager.LoadScene(string.IsNullOrEmpty(backScene) ? MainMenu : backScene);

        public static void Load(string scene) => SceneManager.LoadScene(scene);
    }
}

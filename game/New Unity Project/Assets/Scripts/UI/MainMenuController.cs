using UnityEngine;
using UnityEngine.EventSystems;
using UnityEngine.UI;

namespace MP1.UI
{
    /// <summary>S01 shell: Vocabulary Library (G-004), Exit and the technical test entries work; the other product entries are visibly unavailable.</summary>
    public class MainMenuController : MonoBehaviour
    {
        [SerializeField] Button playButton, libraryButton, typographyButton, sandboxButton, mediaButton, exitButton;

        void Start()
        {
            playButton.onClick.AddListener(() => { Library.VocabularyLibraryController.OpenedForPlay = true; SceneNav.Load("VocabularyLibrary"); });
            libraryButton.onClick.AddListener(() => { Library.VocabularyLibraryController.OpenedForPlay = false; SceneNav.Load("VocabularyLibrary"); });
            typographyButton.onClick.AddListener(() => SceneNav.Load("TypographyInput"));
            sandboxButton.onClick.AddListener(() => SceneNav.Load("GameplaySandbox"));
            mediaButton.onClick.AddListener(() => SceneNav.Load("MediaProbe"));
            exitButton.onClick.AddListener(Quit);
            EventSystem.current.SetSelectedGameObject(playButton.gameObject);
        }

        void Update()
        {
            // Keep keyboard navigation alive after a mouse click on empty space clears the selection.
            if (EventSystem.current.currentSelectedGameObject == null && (Input.GetAxisRaw("Vertical") != 0 || Input.GetKeyDown(KeyCode.Tab)))
                EventSystem.current.SetSelectedGameObject(playButton.gameObject);
        }

        static void Quit()
        {
#if UNITY_EDITOR
            UnityEditor.EditorApplication.isPlaying = false;
#else
            Application.Quit();
#endif
        }
    }
}
